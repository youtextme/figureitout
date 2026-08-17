pip install "git+https://github.com/youtextme/figureitout.git" -q 2>/dev/null || true
export RUN_FORREST_SKIP_SYNC=1
python3 -m runforrestrun --install-global
