#  s = '''
#         <script type="text/Javascript">
#         var name = window.prompt("Do you understand Message?");
#         alert(name + " ?");
#         </script>
#         '''
#         HTML(s)
#         time.sleep(3)
        


from IPython.core.display import display, HTML
from IPython.display import clear_output

def color_print(text, color='black', tag='h1'):
    display(HTML(f"<{tag} style=color:{c}>{t}</{tag}>"))

c = 'green'
t = 'text'

import time

def run(*args):
    for i in range(3):
        clear_output(wait = True)
        color_print(*args)
        time.sleep(2)

import threading

t1 = threading.Thread(target=run, args = [t,c,'h1'])
t1.setDaemon(True)
t1.start()
