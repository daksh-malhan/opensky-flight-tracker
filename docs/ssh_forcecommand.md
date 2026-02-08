
# SSH Viewer-Only Mode (ForceCommand)

This project can be hardened so a remote user can **only** run the viewer (no interactive shell).

## Example `sshd_config` snippet

Edit: `/etc/ssh/sshd_config`

```sshconfig
Match User flightview
    PasswordAuthentication no
    PubkeyAuthentication yes
    AuthenticationMethods publickey

    # Hardening
    PermitTTY no
    X11Forwarding no
    AllowTcpForwarding no
    PermitTunnel no
    GatewayPorts no
    PermitOpen none

    # Viewer-only command
    ForceCommand /usr/bin/python3 /opt/opensky-flight-tracker/viewer.py
```

Reload SSH safely:

```bash
sudo sshd -t && sudo systemctl reload ssh
```

## Notes
- Make sure `/opt/opensky-flight-tracker/viewer.py` exists and is readable/executable.
- If the viewer needs DB env vars, wrap `ForceCommand` like this:

```sshconfig
ForceCommand /usr/bin/env PGHOST=localhost PGDATABASE=flightlogs PGUSER=flightview PGPASSWORD=flightview \
    /usr/bin/python3 /opt/opensky-flight-tracker/viewer.py
```
