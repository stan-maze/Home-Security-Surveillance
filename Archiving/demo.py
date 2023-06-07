from detector import detect_tasks_manager

    
def test():
    manager = detect_tasks_manager()
    manager.run_detect()

if __name__ == '__main__':
    test()