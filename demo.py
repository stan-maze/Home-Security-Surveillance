from detector import detect_tasks_manager

    
def test():
    manager = detect_tasks_manager()
    manager.gen_frame_stream()

if __name__ == '__main__':
    test()