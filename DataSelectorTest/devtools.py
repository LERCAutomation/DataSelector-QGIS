import ptvsd

def attach_ptvsd(port=5678, inject_breakpoint=False):
    try:
        if not ptvsd.is_attached():
            print(f"🛑 Waiting for debugger to attach on port {port}...")
            ptvsd.enable_attach(address=('localhost', port))
            ptvsd.wait_for_attach()
            print("✅ Debugger attached via ptvsd.")
        if inject_breakpoint:
            ptvsd.break_into_debugger()
    except Exception as e:
        print(f"⚠️ ptvsd failed: {e}")
