"""Verify deployed init/proxy images using new disposable volumes and no published ports.

Build deployment images as varal-hmg-validation-{bootstrap,journal,wal,proxy,api}:20261117
before invoking. Only resources with this run's random prefix are stopped or removed.
"""

import json
import secrets
import subprocess
import sys
import uuid

PREFIX = "varal-hmg-qa-" + secrets.token_hex(6)
EPOCH = str(uuid.uuid4())
KEYS = ("chain", "receipt", "checkpoint", "writer", "restore", "fence", "wal-cipher", "wal-witness")
STATE = ("journal", "checkpoint", "wal-spool", "wal-archive", "wal-acks", "wal-anchor")
volumes = set()
containers = []
checks = []


def docker(arguments, expected=0):
    result = subprocess.run(["docker", *arguments], capture_output=True, text=True)
    if result.returncode != expected:
        # These images deliberately suppress credential/document content in their errors.
        raise RuntimeError("Docker check failed: " + result.stderr[-1500:])
    return result.stdout.strip()


def mounts(mapping):
    arguments = []
    for name, target in mapping.items():
        volume = PREFIX + "-" + name
        volumes.add(volume)
        arguments += ["--mount", "type=volume,src=" + volume + ",dst=" + target]
    return arguments


def image(role):
    return "varal-hmg-validation-" + role + ":20261117"


def run(role, mapping, *, entrypoint=None, command=(), epoch=EPOCH, expected=0, detached=False):
    arguments = ["run", "--network", "none", "-e", "JOURNAL_EPOCH=" + epoch]
    if detached:
        name = PREFIX + "-" + role
        arguments += ["-d", "--name", name]
        containers.append(name)
    else:
        arguments.append("--rm")
    arguments += mounts(mapping)
    if entrypoint:
        arguments += ["--entrypoint", entrypoint]
    arguments += [image(role), *command]
    return docker(arguments, expected=expected)


def record(name):
    checks.append(name)
    print("PASS " + name, flush=True)


def helper(mapping, code, **kwargs):
    return run("bootstrap", mapping, entrypoint="python", command=("-c", code), **kwargs)


bootstrap = {"bootstrap": "/bootstrap", "postgres": "/state/postgres"}
bootstrap.update({name: "/state/" + name for name in STATE})
bootstrap.update({"key-" + name: "/keys/" + name for name in KEYS})
journal = {"journal": "/varal/journal", "checkpoint": "/varal/checkpoint"}
journal.update({"key-" + name: "/run/keys/" + name for name in KEYS[:6]})
wal = {name: "/varal/" + name for name in STATE[2:]}
wal.update({"key-" + name: "/run/keys/" + name for name in KEYS[6:]})

try:
    run("bootstrap", bootstrap)
    snapshot = helper(bootstrap, "import hashlib,json,pathlib; print(json.dumps({p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/keys').glob('*/key')},sort_keys=True))")
    assert len(json.loads(snapshot)) == 8
    record("fresh bootstrap creates eight distinct capability files")
    run("bootstrap", bootstrap)
    assert snapshot == helper(bootstrap, "import hashlib,json,pathlib; print(json.dumps({p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/keys').glob('*/key')},sort_keys=True))")
    record("repeated bootstrap preserves capabilities")
    run("bootstrap", bootstrap, epoch=str(uuid.uuid4()), expected=1)
    record("changed epoch refuses reinitialization")
    run("journal", journal, entrypoint="python", command=("/srv/journal/journal-init.py",))
    run("wal", wal, entrypoint="python", command=("/srv/wal-init.py",))
    run("bootstrap", bootstrap, entrypoint="python", command=("/srv/seal.py",))
    run("bootstrap", bootstrap)
    record("journal and encrypted WAL initialize and seal successfully")
    run("journal", journal, command=(
        "--directory", "/varal/journal", "--checkpoint-directory", "/varal/checkpoint", "--epoch", EPOCH,
        *[item for name in KEYS[:6] for item in ("--" + name + "-key-file", "/run/keys/" + name + "/key")],
        "--listen", "127.0.0.1",
    ), detached=True)
    run("wal", wal, command=("--spool", "/varal/wal-spool", "--archive", "/varal/wal-archive", "--acks", "/varal/wal-acks", "--anchor", "/varal/wal-anchor", "--epoch", EPOCH, "--cipher-key", "/run/keys/wal-cipher/key", "--witness-key", "/run/keys/wal-witness/key"), detached=True)
    # A second init must verify complete anchors even while the writers hold their locks.
    run("journal", journal, entrypoint="python", command=("/srv/journal/journal-init.py",))
    run("wal", wal, entrypoint="python", command=("/srv/wal-init.py",))
    docker(["exec", PREFIX + "-journal", "python", "/srv/journal/journal-health.py"])
    docker(["exec", PREFIX + "-wal", "python", "/srv/health.py"])
    record("repeated init coexists with authenticated journal and live WAL writer")
    runtime = {"key-writer": "/keys/writer", "key-receipt": "/keys/receipt", "key-wal-witness": "/keys/wal-witness"}
    arguments = ["run", "--rm", "--network", "none", "--user", "10001:10001", *mounts(runtime), "--entrypoint", "python", image("bootstrap"), "-c", "from pathlib import Path; assert all(len(p.read_bytes().strip())==64 for p in Path('/keys').glob('*/key'))"]
    docker(arguments)
    record("non-root runtime can read only its mounted capability files")
    run("api", {"staging": "/varal/staging", "beat": "/varal/beat", "migration-lock": "/varal/lock"}, entrypoint="python", command=("-c", "import os; from pathlib import Path; assert os.getuid()==10001; [(Path('/varal')/n/'probe').write_text('synthetic') for n in ('staging','beat','lock')]"))
    record("new staging beat and migration volumes are writable by UID10001")
    for role in ("edge", "ssr"):
        command = "envsubst '$VARAL_DOMAIN $VARAL_STACK $COOLIFY_PROXY_TRUST $VARAL_WEB_IP' < /etc/varal/" + role + ".conf.template > /tmp/nginx.conf && nginx -t -c /tmp/nginx.conf"
        docker(["run", "--rm", "--network", "none", "--add-host", "hmgvaral-api:127.0.0.1", "--add-host", "hmgvaral-web:127.0.0.1", "-e", "VARAL_STACK=hmgvaral", "-e", "VARAL_DOMAIN=hmgvaral.codehub.systems", "-e", "COOLIFY_PROXY_TRUST=172.18.0.2/32", "-e", "VARAL_WEB_IP=172.30.212.10", "--entrypoint", "/bin/sh", image("proxy"), "-c", command])
    record("edge and restricted SSR nginx configuration validates")
    helper(bootstrap, "from pathlib import Path; Path('/bootstrap/database.ready').write_text('synthetic')")
    run("bootstrap", bootstrap, expected=1)
    record("lost initialized PostgreSQL volume refuses automatic recreation")
    helper(bootstrap, "from pathlib import Path; Path('/bootstrap/database.ready').unlink(); Path('/state/journal/journal.jsonl').unlink()")
    run("bootstrap", bootstrap, expected=1)
    record("lost sealed journal refuses automatic recreation")
    partial = {"partial-bootstrap": "/bootstrap", "partial-postgres": "/state/postgres"}
    partial.update({"partial-" + name: "/state/" + name for name in STATE})
    partial.update({"partial-key-" + name: "/keys/" + name for name in KEYS})
    helper(partial, "from pathlib import Path; Path('/keys/writer/key').write_text('synthetic-partial')")
    run("bootstrap", partial, expected=1)
    record("partial capability initialization refuses regeneration")
    print(json.dumps({"prefix": PREFIX, "passed": len(checks), "checks": checks}, ensure_ascii=True), flush=True)
except Exception as error:
    print(str(error), file=sys.stderr)
    sys.exit(1)
finally:
    for name in containers:
        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for name in sorted(volumes):
        subprocess.run(["docker", "volume", "rm", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
