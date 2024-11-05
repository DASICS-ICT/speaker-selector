import argparse
import random
import socket
import http.server
import urllib.parse
from urllib.parse import parse_qs
import socketserver
import json

current_log = ""

def load_weights(weights_file):
    if not weights_file:
        return {}
    weights = {}
    try:
        with open(weights_file, 'r') as f:
            for line in f.readlines():
                name, weight = line.strip().split(',')
                weights[name] = int(weight)
    except FileNotFoundError:
        print('%s not found, create a new one!'%weights_file)
    return weights

def save_weights(weights_file, weights):
    if not weights_file:
        return
    with open(weights_file, 'w') as f:
        for name, weight in weights.items():
            f.write('{},{}\n'.format(name, weight))

def log_str(_s, history_file):
    global current_log
    history_file.write(_s)
    current_log += _s
def dump_weights(weights, history_file):
    log_str("[ WEIGHTS LOG ]\n", history_file)
    for name, weight in weights.items():
        log_str('{},{}\n'.format(name, weight), history_file)
def get_speaker(weights, args, volunteer=None):
    names = weights.keys()
    with open(args.history_log_file, 'a') as history_file:
        global current_log
        current_log = ""
        log_str("======================================\n", history_file)
        for name in names:
            weights[name] *= 2
        dump_weights(weights, history_file)
        if volunteer and volunteer in names:
            weights[volunteer] = 1
            log_str("[PICK] choose volunteer: %s \n" % volunteer, history_file)
            return volunteer
        else:
            total_weight = sum(weights.values())
            rand = random.uniform(0, total_weight)
            weight_sum = 0
            log_str("[RAND PROCEDURE] random number: %d\n" % rand, history_file)
            for name, weight in weights.items():
                weight_sum += weight
                log_str("[RAND PROCEDURE] weight_sum: %d name %s\n" % (weight_sum, name), history_file)
                if rand <= weight_sum:
                    weights[name] = 1
                    log_str("[PICK] random result: %s\n" % name, history_file)
                    return name
            return None

class RequestHandler(http.server.BaseHTTPRequestHandler):
    html_page = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Speaker Selector</title>
        <meta charset="UTF-8">
        <style>
            body {
                background-color: #f2f2f2;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 1em;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .form-container {
                margin: 0 auto;
                background-color: #fff;
                border-radius: 0.5em;
                box-shadow: 0 0.2em 0.5em rgba(0, 0, 0, 0.2);
                padding: 2em;
                max-width: 30em;
                width: 100%;
                text-align: center;
            }
            h1 {
                margin: 0;
                padding: 0.5em;
                background-color: #1d1d1d;
                color: #fff;
                text-align: center;
                border-top-left-radius: 0.5em;
                border-top-right-radius: 0.5em;
                box-shadow: 0 0.2em 0.5em rgba(0, 0, 0, 0.2);
                font-size: 2.5em;
                margin-bottom: 1em;
            }
            .form-container label {
                font-weight: bold;
                display: block;
                margin-bottom: 0.5em;
                color: #333;
                text-align: left;
            }
            .form-container select {
                font-size: 1.2em;
                padding: 0.5em;
                margin-bottom: 1em;
                width: 100%;
                border-radius: 0.2em;
                border: 1px solid #ccc;
            }
            .form-container button {
                font-size: 1.2em;
                padding: 0.5em;
                background-color: #1d1d1d;
                color: white;
                border: none;
                cursor: pointer;
                width: 100%;
                border-radius: 0.2em;
                transition: background-color 0.2s;
            }
            .form-container button:hover {
                background-color: #333;
            }
            .form-container #log-area button {
                margin-top: 0.2em;
                margin-bottom: 0.2em;
            }
            .form-container #log-area hr {
                border: none;
                border-top: 1px solid #ccc;
                margin: 0.5em 0;
                margin-top: 1em;
                margin-bottom: 1em;
            }
            #speaker-name {
                font-size: 1.5em;
                margin-top: 1em;
                padding: 0.5em;
                background-color: #f2f2f2;
                border: 1px solid #ccc;
                text-align: center;
                display: none;
                border-radius: 0.2em;
                box-shadow: 0 0.2em 0.5em rgba(0, 0, 0, 0.2);
            }
            .weight-container {
                margin-top: 1em;
                text-align: left;
                border: none;
                padding: 0;
                background-color: #f2f2f2;
                border-radius: 0.2em;
                box-shadow: 0 0.2em 0.5em rgba(0, 0, 0, 0.2);
            }

            .weight-container hr {
                border: none;
                border-top: 1px solid #ccc;
                margin: 0.5em 0;
            }

            .weight-container label {
                font-weight: bold;
                display: block;
                margin: 0.5em 0;
                padding: 0 1em;
            }

            .weight-container span {
                display: inline-block;
                width: 3em;
                text-align: center;
                margin-left: 1em;
                padding: 0.5em;
                background-color: #f2f2f2;
            }

            /* Add animation to "page content" */
            .animate-bottom {
              position: relative;
              -webkit-animation-name: animatebottom;
              -webkit-animation-duration: 1s;
              animation-name: animatebottom;
              animation-duration: 1s
            }
            
            @-webkit-keyframes animatebottom {
              from { bottom:-10px; opacity:0 }
              to { bottom:0px; opacity:1 }
            }
            
            @keyframes animatebottom {
              from{ bottom:-10px; opacity:0 }
              to{ bottom:0; opacity:1 }
            }

            #logContent textarea {
              width: 100%;
              height: 400px;
              padding: 12px 20px;
              box-sizing: border-box;
            
              border: 2px solid #ccc;
              border-radius: 4px;
            
              background-color: #f8f8f8;
              resize: none;
            
              font-size: 16px;
              color: #555;
            }
            
            /* Focus state */
            #logContent textarea:focus {
              border-color: #333;
              outline: none;
            }
            
            /* Valid/invalid styles */
            #logContent textarea.valid {
              border-color: #28a745;
            }
            
            #logContent textarea.invalid {
              border-color: #dc3545;
            }
            
            /* Border animation on focus */
            #logContent textarea:focus {
              border-color: #007bff;
              transition: border-color 0.15s ease-in-out;
            }
            
            #logContent textarea[readonly] {
              background-color: #fff;
              cursor: not-allowed;
              border-color: #ccc;
            }
            
            #logContent textarea[readonly]:hover {
              border-color: #ccc;
            }
            
            #logContent textarea[readonly]:focus {
              border-color: #ccc;
              box-shadow: none;
            }
        </style>
    </head>
    <body>
        <div class="form-container">
            <h1>Speaker Selector</h1>
            <form id="speaker-selector">
                <label for="volunteer">Select a volunteer speaker:</label>
                <select id="volunteer" name="volunteer">
                    <option value="">-- None --</option>
                    {{all_names_html}}
                </select>
                <div class="weight-container" id="weight-container">
                    {{all_weights_html}}
                </div>
                <button>Select Speaker</button>
            </form>
            <div id="speaker-name"></div>
            <hr/>
            <div id="log-area">
                <button id="history-btn">Show History</button>
                <button id="curr-log-btn">Show Current Log</button>
                <button id="all-log-btn">Show All Log</button>
                <div id="logContent"> </div>
            </div>
        </div>
        <script>
            function selectSpeaker(event) {
                event.preventDefault();
                var volunteer = document.getElementById('volunteer').value;
                var xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        var data = JSON.parse(this.responseText);
                        if ('speaker' in data) {
                            var speakerName = document.getElementById('speaker-name');
                            speakerName.textContent = 'The next speaker is ' + data['speaker'];
                            speakerName.style.display = 'block';
                            if (data.updated) {
                                updateWeights(data.new_weights_lists); 
                            }
                        } else if ('error' in data) {
                            alert(data['error']);
                        }
                    }
                };
                xhr.open('POST', window.location.href, true);
                xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
                xhr.send('volunteer=' + encodeURIComponent(volunteer));
            }

            function updateWeights(new_weights) {
                let container = document.getElementById('weight-container');
                // 设置新的权重HTML
                let html = '';
                var items = Object.keys(new_weights).map(function(key) {
                    return [key, new_weights[key]];
                });
                items.sort(function(first, second) {
                  return second[1] - first[1];
                });
                var total_weights = 0;
                for (var i = 0; i < items.length; ++i) {
                    total_weights += items[i][1];
                }
                for(var i=0; i<items.length; ++i) {
                  html += `
                    <label>${items[i][0]} <span>${items[i][1]}</span> <span>${(items[i][1]/total_weights).toFixed(2)}</span></label>
                  `;
                }
                container.classList.add('animate-bottom');
                container.innerHTML = html

                // 动画结束后移除类
                setTimeout(() => {
                  let container = document.getElementById('weight-container');
                  // container.innerHTML = html;
                  container.classList.remove('animate-bottom');
                }, 1000);
            }
            function showLog(log_type) {
              // 获取日志
              var xhr = new XMLHttpRequest();
              if (log_type == "curr_log") {
                xhr.open('GET', '/curr_log');
              } else if (log_type == "all_log"){
                xhr.open('GET', '/all_log');
              } else if (log_type == "all_history"){
                xhr.open('GET', '/all_history');
              }
              xhr.onload = function() {
                if (xhr.status === 200) {
                  document.getElementById("logContent").innerHTML = xhr.responseText;
                }
              }
              xhr.send();
            }
            function currLogBtnOnClick() {showLog("curr_log");}
            function allLogBtnOnClick() {showLog("all_log");}
            function historyBtnOnClick() {showLog("all_history");}

            document.addEventListener('DOMContentLoaded', function() {
                var form = document.getElementById('speaker-selector');
                form.addEventListener('submit', selectSpeaker);
                document.getElementById('curr-log-btn').addEventListener('click', currLogBtnOnClick)
                document.getElementById('all-log-btn').addEventListener('click', allLogBtnOnClick)
                document.getElementById('history-btn').addEventListener('click', historyBtnOnClick)
            });
        </script>
    </body>
    </html>
    '''
    
    def __init__(self, request, client_address, server):
        self.weights = server.weights
        self.args = server.args
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path == '/curr_log':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(("<textarea readonly>"+current_log+"</textarea>").encode('UTF8'))
        elif self.path == '/all_log':
            with open(self.args.history_log_file, 'r') as history_file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                self.wfile.write(("<textarea readonly>"+history_file.read()+"</textarea>").encode('UTF8'))
                # for line in history_file.readlines():
                #     self.wfile.write(("<pre> </pre>").encode('UTF8'))
        elif self.path == '/all_history':
            with open(self.args.history_log_file, 'r') as history_file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                history_text = ""
                for line in history_file:
                    if "[PICK]" in line:
                        history_text += line[22:]

                self.wfile.write(("<textarea readonly>"+history_text+"</textarea>").encode('UTF8'))
        else:
            # 渲染 html 页面
            names = sorted(list(self.weights.keys()))
            total_weights = sum([int(_weight) for _,_weight in self.weights.items()])
            names_json = json.dumps(names)
            response = self.html_page.replace('{{names_json}}', names_json)
            all_names_html = "\n".join([
                '<option value="{{name}}">{{name}}</option>'.replace('{{name}}',name) for name in names])
            response = response.replace('{{all_names_html}}', all_names_html)
            # sorted by weight
            all_weights_html = "<hr>\n".join([
                '<label> %s <span>%s</span> <span>%.2f</span> </label>'%(name, weight, float(weight)/total_weights) for name, weight in sorted(self.weights.items(), reverse=True, key=lambda x:x[1])])
            response = response.replace('{{all_weights_html}}', all_weights_html)
            response = response.encode()

            # 发送 html 页面给客户端
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def do_POST(self):
        # 从请求体中获取志愿者的值
        content_length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(content_length)
        params = parse_qs(body.decode())
        volunteer = params.get('volunteer', [None])[0]
        print(volunteer)

        # 选择演讲者并返回结果
        name = get_speaker(self.weights, self.args, volunteer)
        if name:
            self.weights[name] = 1
            save_weights(self.args.weights_file, self.weights)
            response = {'speaker': name, 'updated': True, 'new_weights_lists': self.weights}
        else:
            response = {'error': 'No speaker available'}
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def run_cli(weights, args):
    print('Select a volunteer speaker or leave blank:')
    final_names = sorted(list(weights.keys()))
    for i, name in enumerate(final_names):
        print('{}) {}'.format(i+1, name))
    volunteer = input('> ').strip()
    if volunteer:
        try:
            volunteer_idx = int(volunteer) - 1
            volunteer = final_names[volunteer_idx]
        except (ValueError, IndexError):
            print('Invalid input, use default weights')
            volunteer = None
    name = get_speaker(weights, args, volunteer)
    if name:
        weights[name] = 1
        save_weights(args.weights_file, weights)
        print('The next speaker is ', name)
    else:
        print('No speaker available')

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def run_network(weights, args):
    RequestHandler.weights = weights
    RequestHandler.args = args
    server_address = (args.server, args.port)
    httpd = ThreadedHTTPServer(server_address, RequestHandler)
    httpd.weights = weights  # 把权重数据传递给服务器
    httpd.args = args
    host_name = socket.gethostname()
    # host_ip = socket.gethostbyname(host_name)
    host_ip = args.server
    print(f'Starting server on {host_name} ({host_ip}), port {args.port}...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Server stopped.')

def main():
    parser = argparse.ArgumentParser(description='Randomly select a speaker from a list of names')
    parser.add_argument('--weights', dest='weights_file', default='weights.txt',
                        help='file containing speaker weights (default: weights.txt)')
    parser.add_argument('--history', dest='history_log_file', default='history.txt',
                        help='file containing logs and history (default: history.txt)')
    parser.add_argument('--interface', dest='interface', choices=['cli', 'network'], default='cli',
                        help='interface to use (default: cli)')
    parser.add_argument('--port', type=int, default=8000,
                        help='port number (default: 8000)')
    parser.add_argument('--server', type=str, default='127.0.0.1',
                        help='server address (default: 127.0.0.1)')
    parser.add_argument('names', nargs='*', help='list of speaker names')
    args = parser.parse_args()

    weights = load_weights(args.weights_file)
    for name in args.names:
        weights[name] = 1

    if args.interface == 'cli':
        run_cli(weights, args)
    elif args.interface == 'network':
        run_network(weights, args)

if __name__ == '__main__':
    main()
