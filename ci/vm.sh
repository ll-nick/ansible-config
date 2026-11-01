#!/usr/bin/env bash
# A disposable Ubuntu desktop VM for testing what the Docker harness cannot:
# the GNOME session, systemd user units and a real sudo password prompt.
#
# Usage: ci/vm.sh <command>
#
#   create            Download Ubuntu and provision the clean base image (slow, once)
#   start [--headless]  Boot the VM, in a window unless headless
#   stop              Shut the VM down
#   reset             Discard all changes made in the VM and stop it
#   ssh [--display] [command...]
#                     Open a shell in the VM; --display joins the desktop session
#   sync [branch]     Push a branch (default: current) into the VM, ready to deploy
#   status            Show the state of the VM
#   destroy           Delete the VM, its base image and the downloaded image
#
# Log in with tester / tester, which is also the sudo password.
#
# Requires KVM, and QEMU with genisoimage (on Ubuntu:
# apt install qemu-system-x86 qemu-utils genisoimage), or Nix to fetch them.
#
# Settings: DEVSTACK_VM_MEMORY_MB, DEVSTACK_VM_CPUS, DEVSTACK_VM_SSH_PORT,
# DEVSTACK_VM_DISK_SIZE, DEVSTACK_VM_UBUNTU_RELEASE

set -euo pipefail

MEMORY_MB="${DEVSTACK_VM_MEMORY_MB:-6144}"
CPUS="${DEVSTACK_VM_CPUS:-4}"
SSH_PORT="${DEVSTACK_VM_SSH_PORT:-2222}"
DISK_SIZE="${DEVSTACK_VM_DISK_SIZE:-40G}"
UBUNTU_RELEASE="${DEVSTACK_VM_UBUNTU_RELEASE:-resolute}"

VM_USER="tester"
VM_PASSWORD="tester"
VM_HOSTNAME="devstack-vm"
VM_REPOSITORY="devstack.git"
PROVISIONED_MARKER="DEVSTACK_VM_PROVISIONED"
PROVISIONING_TIMEOUT="45m"
BOOT_TIMEOUT_SECONDS=240
SHUTDOWN_TIMEOUT_SECONDS=60

CLOUD_IMAGE_NAME="$UBUNTU_RELEASE-server-cloudimg-amd64.img"
CLOUD_IMAGE_BASE_URL="https://cloud-images.ubuntu.com/$UBUNTU_RELEASE/current"

STATE_DIRECTORY="${XDG_CACHE_HOME:-$HOME/.cache}/devstack-vm"
CLOUD_IMAGE="$STATE_DIRECTORY/$CLOUD_IMAGE_NAME"
BASE_IMAGE="$STATE_DIRECTORY/base-$UBUNTU_RELEASE.qcow2"
OVERLAY_IMAGE="$STATE_DIRECTORY/overlay.qcow2"
SSH_KEY="$STATE_DIRECTORY/id_ed25519"
PID_FILE="$STATE_DIRECTORY/qemu.pid"
QEMU_LOG="$STATE_DIRECTORY/qemu.log"
SERIAL_LOG="$STATE_DIRECTORY/serial.log"
PROVISIONING_LOG="$STATE_DIRECTORY/provisioning.log"

WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_OPTIONS=(
    -i "$SSH_KEY"
    -o IdentitiesOnly=yes
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o LogLevel=ERROR
)

fail() {
    printf 'error: %s\n' "$1" >&2
    exit 1
}

print_usage() {
    sed -n '/^# Usage:/,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

ensure_tools() {
    if command -v qemu-system-x86_64 > /dev/null && command -v qemu-img > /dev/null \
        && command -v genisoimage > /dev/null; then
        return
    fi
    if [ -z "${DEVSTACK_VM_IN_NIX_SHELL:-}" ] && command -v nix > /dev/null; then
        DEVSTACK_VM_IN_NIX_SHELL=1 exec nix \
            --extra-experimental-features "nix-command flakes" \
            shell nixpkgs#qemu_kvm nixpkgs#cdrkit -c "${BASH_SOURCE[0]}" "$@"
    fi
    fail "qemu-system-x86_64, qemu-img and genisoimage are required"
}

ensure_kvm() {
    [ -r /dev/kvm ] && [ -w /dev/kvm ] \
        || fail "/dev/kvm is not accessible, is your user in the kvm group?"
}

is_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2> /dev/null
}

is_provisioned() {
    [ -f "$BASE_IMAGE" ]
}

download_cloud_image() {
    if [ -f "$CLOUD_IMAGE" ]; then
        return
    fi
    printf 'Downloading %s...\n' "$CLOUD_IMAGE_NAME"
    curl --fail --location --progress-bar \
        --output "$CLOUD_IMAGE.partial" "$CLOUD_IMAGE_BASE_URL/$CLOUD_IMAGE_NAME"

    local expected_checksum
    expected_checksum="$(curl --fail --silent --show-error --location \
        "$CLOUD_IMAGE_BASE_URL/SHA256SUMS" \
        | awk -v name="$CLOUD_IMAGE_NAME" '$2 == "*" name || $2 == name { print $1 }')"
    [ -n "$expected_checksum" ] || fail "no checksum published for $CLOUD_IMAGE_NAME"
    printf '%s  %s\n' "$expected_checksum" "$CLOUD_IMAGE.partial" | sha256sum --check --quiet \
        || fail "checksum mismatch for $CLOUD_IMAGE_NAME"
    mv "$CLOUD_IMAGE.partial" "$CLOUD_IMAGE"
}

write_seed_image() {
    local seed_image="$1"
    local seed_directory
    seed_directory="$(mktemp -d)"
    printf 'instance-id: %s\nlocal-hostname: %s\n' "$VM_HOSTNAME" "$VM_HOSTNAME" \
        > "$seed_directory/meta-data"
    # sudo deliberately asks for a password, which the Docker harness never does.
    # inkscape, flatpak and libnotify-bin enable the inkflow component, the flatpak
    # update step and desktop notifications.
    cat > "$seed_directory/user-data" << EOF
#cloud-config
users:
  - name: $VM_USER
    groups: [sudo]
    shell: /bin/bash
    lock_passwd: false
    ssh_authorized_keys:
      - $(cat "$SSH_KEY.pub")
chpasswd:
  expire: false
  users:
    - { name: $VM_USER, password: $VM_PASSWORD, type: text }
ssh_pwauth: false
package_update: true
packages:
  - ubuntu-desktop-minimal
  - openssh-server
  - git
  - curl
  - inkscape
  - flatpak
  - libnotify-bin
write_files:
  - path: /etc/gdm3/custom.conf
    content: |
      [daemon]
      AutomaticLoginEnable=true
      AutomaticLogin=$VM_USER
runcmd:
  - systemctl set-default graphical.target
  - dpkg -s ubuntu-desktop-minimal > /dev/null && echo "$PROVISIONED_MARKER" > /dev/ttyS0
power_state:
  mode: poweroff
  condition: true
EOF
    genisoimage -quiet -output "$seed_image" -volid cidata -joliet -rock \
        "$seed_directory/user-data" "$seed_directory/meta-data"
    rm -rf "$seed_directory"
}

create_vm() {
    ensure_kvm
    if is_provisioned; then
        printf 'The base image already exists, use reset for a clean VM.\n'
        return
    fi
    mkdir -p "$STATE_DIRECTORY"
    [ -f "$SSH_KEY" ] || ssh-keygen -q -t ed25519 -N '' -C "$VM_HOSTNAME" -f "$SSH_KEY"
    download_cloud_image

    local provisioning_image="$BASE_IMAGE.provisioning"
    local seed_image="$STATE_DIRECTORY/seed.iso"
    cp "$CLOUD_IMAGE" "$provisioning_image"
    qemu-img resize -q "$provisioning_image" "$DISK_SIZE"
    write_seed_image "$seed_image"

    printf 'Provisioning the base image, this takes a while (log: %s)...\n' "$PROVISIONING_LOG"
    timeout "$PROVISIONING_TIMEOUT" qemu-system-x86_64 \
        -enable-kvm -cpu host -m "$MEMORY_MB" -smp "$CPUS" \
        -drive "file=$provisioning_image,if=virtio,format=qcow2" \
        -drive "file=$seed_image,if=virtio,format=raw,readonly=on" \
        -netdev user,id=network0 -device virtio-net-pci,netdev=network0 \
        -display none -serial "file:$PROVISIONING_LOG" -no-reboot \
        || fail "provisioning did not finish, see $PROVISIONING_LOG"
    grep -q "$PROVISIONED_MARKER" "$PROVISIONING_LOG" \
        || fail "provisioning failed, see $PROVISIONING_LOG"

    rm -f "$seed_image"
    mv "$provisioning_image" "$BASE_IMAGE"
    printf 'Base image ready. Next: %s start\n' "$0"
}

ensure_overlay() {
    if [ ! -f "$OVERLAY_IMAGE" ]; then
        qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$OVERLAY_IMAGE"
    fi
}

wait_for_ssh() {
    printf 'Waiting for the VM to boot'
    local deadline=$((SECONDS + BOOT_TIMEOUT_SECONDS))
    until ssh "${SSH_OPTIONS[@]}" -o ConnectTimeout=2 -o BatchMode=yes -p "$SSH_PORT" \
        "$VM_USER@127.0.0.1" true 2> /dev/null; do
        if ! is_running; then
            printf '\n'
            fail "the VM exited, see $QEMU_LOG"
        fi
        if [ "$SECONDS" -ge "$deadline" ]; then
            printf '\n'
            fail "no SSH after ${BOOT_TIMEOUT_SECONDS}s, see $SERIAL_LOG"
        fi
        printf '.'
        sleep 2
    done
    printf ' up\n'
}

start_vm() {
    local display="gtk"
    case "${1:-}" in
        --headless) display="none" ;;
        "") ;;
        *) fail "unknown option for start: $1" ;;
    esac

    ensure_kvm
    is_provisioned || fail "no base image yet, run: $0 create"
    if is_running; then
        printf 'The VM is already running.\n'
        return
    fi
    ensure_overlay

    # The desktop needs a display adapter even when no window shows it
    setsid nohup qemu-system-x86_64 \
        -name "$VM_HOSTNAME" \
        -enable-kvm -cpu host -m "$MEMORY_MB" -smp "$CPUS" \
        -drive "file=$OVERLAY_IMAGE,if=virtio,format=qcow2" \
        -netdev "user,id=network0,hostfwd=tcp:127.0.0.1:$SSH_PORT-:22" \
        -device virtio-net-pci,netdev=network0 \
        -device virtio-vga -device qemu-xhci -device usb-tablet \
        -display "$display" \
        -serial "file:$SERIAL_LOG" \
        -pidfile "$PID_FILE" \
        > "$QEMU_LOG" 2>&1 < /dev/null &
    sleep 1
    wait_for_ssh

    printf '\nThe VM is running. Log in with %s / %s.\n' "$VM_USER" "$VM_PASSWORD"
    printf 'To test a branch: %s sync\n' "$0"
}

stop_vm() {
    if ! is_running; then
        printf 'The VM is not running.\n'
        rm -f "$PID_FILE"
        return
    fi
    ssh "${SSH_OPTIONS[@]}" -o ConnectTimeout=5 -p "$SSH_PORT" "$VM_USER@127.0.0.1" \
        "echo $VM_PASSWORD | sudo -S -p '' systemctl poweroff" 2> /dev/null || true

    local deadline=$((SECONDS + SHUTDOWN_TIMEOUT_SECONDS))
    while is_running && [ "$SECONDS" -lt "$deadline" ]; do
        sleep 1
    done
    if is_running; then
        printf 'The VM did not shut down, stopping QEMU.\n'
        kill "$(cat "$PID_FILE")"
    fi
    rm -f "$PID_FILE"
    printf 'The VM is stopped.\n'
}

kill_vm() {
    if is_running; then
        local qemu_pid
        qemu_pid="$(cat "$PID_FILE")"
        kill "$qemu_pid"
        while kill -0 "$qemu_pid" 2> /dev/null; do
            sleep 0.2
        done
    fi
    rm -f "$PID_FILE"
}

reset_vm() {
    kill_vm
    rm -f "$OVERLAY_IMAGE"
    printf 'The VM is back to its clean state. Next: %s start\n' "$0"
}

destroy_vm() {
    kill_vm
    rm -rf "$STATE_DIRECTORY"
    printf 'Deleted %s\n' "$STATE_DIRECTORY"
}

ssh_into_vm() {
    is_running || fail "the VM is not running, run: $0 start"
    local environment=""
    if [ "${1:-}" = "--display" ]; then
        shift
        environment="export XDG_RUNTIME_DIR=/run/user/\$(id -u)"
        environment+=" DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/\$(id -u)/bus"
        environment+=" WAYLAND_DISPLAY=wayland-0; "
    fi
    if [ "$#" -gt 0 ]; then
        exec ssh "${SSH_OPTIONS[@]}" -t -p "$SSH_PORT" "$VM_USER@127.0.0.1" \
            "$environment$*"
    fi
    exec ssh "${SSH_OPTIONS[@]}" -t -p "$SSH_PORT" "$VM_USER@127.0.0.1" \
        "${environment}exec bash -l"
}

sync_branch() {
    is_running || fail "the VM is not running, run: $0 start"
    local branch="${1:-$(git -C "$WORKSPACE" symbolic-ref --short HEAD)}"
    git -C "$WORKSPACE" rev-parse --verify --quiet "refs/heads/$branch" > /dev/null \
        || fail "no local branch named $branch"
    if [ -n "$(git -C "$WORKSPACE" status --porcelain)" ]; then
        printf 'warning: uncommitted changes are not part of the push\n' >&2
    fi

    local remote_command="git init --quiet --bare ~/$VM_REPOSITORY"
    remote_command+=" && git -C ~/$VM_REPOSITORY symbolic-ref HEAD refs/heads/$branch"
    ssh "${SSH_OPTIONS[@]}" -p "$SSH_PORT" "$VM_USER@127.0.0.1" "$remote_command"
    GIT_SSH_COMMAND="ssh ${SSH_OPTIONS[*]}" git -C "$WORKSPACE" push --quiet --force \
        "ssh://$VM_USER@127.0.0.1:$SSH_PORT/home/$VM_USER/$VM_REPOSITORY" \
        "refs/heads/$branch:refs/heads/$branch"
    git -C "$WORKSPACE" show "refs/heads/$branch:deploy/deploy.sh" \
        | ssh "${SSH_OPTIONS[@]}" -p "$SSH_PORT" "$VM_USER@127.0.0.1" "cat > ~/deploy.sh"

    printf 'Pushed %s. In a terminal on the VM desktop, run:\n\n' "$branch"
    printf '  sh ~/deploy.sh --repository ~/%s --branch %s --privileged\n\n' \
        "$VM_REPOSITORY" "$branch"
}

show_status() {
    if is_provisioned; then
        printf 'base image: %s\n' "$BASE_IMAGE"
    else
        printf 'base image: none, run: %s create\n' "$0"
    fi
    if [ -f "$OVERLAY_IMAGE" ]; then
        printf 'changes:    %s\n' "$(du -h "$OVERLAY_IMAGE" | cut -f1)"
    else
        printf 'changes:    none\n'
    fi
    if is_running; then
        printf 'state:      running, SSH on 127.0.0.1:%s\n' "$SSH_PORT"
    else
        printf 'state:      stopped\n'
    fi
}

COMMAND="${1:-}"
[ "$#" -eq 0 ] || shift

case "$COMMAND" in
    create | start | reset) ensure_tools "$COMMAND" "$@" ;;
esac

case "$COMMAND" in
    create) create_vm ;;
    start) start_vm "$@" ;;
    stop) stop_vm ;;
    reset) reset_vm ;;
    ssh) ssh_into_vm "$@" ;;
    sync) sync_branch "$@" ;;
    status) show_status ;;
    destroy) destroy_vm ;;
    "" | -h | --help | help) print_usage ;;
    *)
        print_usage >&2
        exit 1
        ;;
esac
