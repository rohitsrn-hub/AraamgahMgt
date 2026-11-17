# Keep the retired live-server tests out of the default run (`pytest tests/`).
collect_ignore_glob = ["legacy_live_server/*"]
