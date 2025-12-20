import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        """
        Из файла загрузить задачи
        """
        if os.path.exists('tasks.txt'):
            try:
                with open('tasks.txt', 'r') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.next_id = data.get('next_id', 1)
            except (json.JSONDecodeError, KeyError):
                self.tasks = []
                self.next_id = 1

    def save_tasks(self):
        """
        записываю задачи в файлик
        """
        data = {
            'tasks': self.tasks,
            'next_id': self.next_id
        }
        with open('tasks.txt', 'w') as f:
            json.dump(data, f)

    def create_task(self, title, priority):
        """
        новая задача"""
        if priority not in ['low', 'normal', 'high']:
            return None

        task = {
            'id': self.next_id,
            'title': title,
            'priority': priority,
            'isDone': False
        }
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task

    def get_all_tasks(self):
        """возвращает все задачи
        """
        return self.tasks

    def complete_task(self, task_id):
        """отметка задачи как выполненую"""
        for task in self.tasks:
            if task['id'] == task_id:
                task['isDone'] = True
                self.save_tasks()
                return True
        return False


class TaskHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, task_manager=None, **kwargs):
        self.task_manager = task_manager
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Get запрос"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/tasks':
            self.get_all_tasks()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Post-запросы"""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')

        if parsed_path.path == '/tasks' and len(path_parts) == 2:
            self.create_task()
        elif len(path_parts) == 4 and path_parts[1] == 'tasks' and path_parts[3] == 'complete':
            try:
                task_id = int(path_parts[2])
                self.complete_task(task_id)
            except ValueError:
                self.send_error(400, "Invalid task ID")
        else:
            self.send_error(404, "Not Found")

    def get_all_tasks(self):
        """список всех задач"""
        tasks = self.task_manager.get_all_tasks()
        response = json.dumps(tasks).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def create_task(self):
        """создает новую задачу"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "empty")
            return

        try:
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "invalid")
            return

        if 'title' not in data or 'priority' not in data:
            self.send_error(400, "title")
            return

        task = self.task_manager.create_task(data['title'], data['priority'])
        if task is None:
            self.send_error(400, "'low' 'normal' 'high'")
            return

        response = json.dumps(task).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def complete_task(self, task_id):
        """
        отмечает задачу как выполненную ещё раз"""
        if self.task_manager.complete_task(task_id):
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.end_headers()
        else:
            self.send_error(404, "Task not found")

    def log_message(self, format, *args):
        """Вырубить логирование - база
        """
        pass


def run_server(port=8000):
    """
        запуск сервера
    """
    task_manager = TaskManager()

    def handler(*args, **kwargs):
        return TaskHTTPHandler(*args, task_manager=task_manager, **kwargs)

    server = HTTPServer(('localhost', port), handler)
    print(f"Ya zapustilsya ura http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == '__main__':
    run_server()
