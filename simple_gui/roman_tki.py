#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog
from threading import Thread
from queue import Queue, Empty

from apluslms_roman import CourseConfig, Builder
from apluslms_roman.logging import SimpleOutput


UPDATE_INTERVAL = 40
FILE_TYPES = (
    ('Course config', '*.yml *.yaml *.json'),
    ('All files', '*'),
)


class QueueStream:
    def __init__(self, queue):
        self.q = queue
    def write(self, msg):
        self.q.put(msg)


class Console(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.text = text = tk.Text(self, height=24, width=80)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll = scroll = tk.Scrollbar(self)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        scroll.config(command=text.yview)
        text.config(yscrollcommand=scroll.set)

    def write(self, line):
        self.text.insert(tk.END, line.rstrip() + '\n')
        self.text.see(tk.END)


class Roman:
    def __init__(self, master):
        self.master = master
        master.protocol("WM_DELETE_WINDOW", self.quit)
        master.title("Roman - A+ LMS course builder")

        cols = 3

        self.config = None
        self.builder_task = None

        self.label = tk.Label(master, text="No course selected!")
        self.label.grid(columnspan=cols, sticky=tk.W)

        # Buttons
        self.course_btn = tk.Button(master, text="Open course", command=self.open)
        self.course_btn.grid(row=1)
        self.build_btn = tk.Button(master, text="Build course", command=self.build, state=tk.DISABLED)
        self.build_btn.grid(row=1, column=1)
        self.close_btn = tk.Button(master, text="Quit", command=master.quit)
        self.close_btn.grid(row=1, column=2)

        # Console output
        self.console = Console(master)
        self.console.grid(columnspan=cols, row=2)

        # Status line
        self.status = tk.Label(master, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(columnspan=cols, row=3, sticky=tk.W+tk.E+tk.S)

        self.set_status("No course selected")

    def set_status(self, msg):
        self.status.config(text=msg.strip())
        self.status.update_idletasks()

    def lock(self):
        self.course_btn.config(state=tk.DISABLED)
        self.build_btn.config(state=tk.DISABLED)
        self.close_btn.config(state=tk.DISABLED)

    def unlock(self):
        self.course_btn.config(state=tk.NORMAL)
        if self.config:
            self.build_btn.config(state=tk.NORMAL)
        self.close_btn.config(state=tk.NORMAL)

    def open(self):
        #file_ = filedialog.askopenfilename(filetypes=FILE_TYPES)
        dir_ = filedialog.askdirectory()
        if not dir_: return

        self.config = CourseConfig.find_from(dir_)

        self.label.config(text="Course: {}".format(self.config.name))
        self.set_status('course opened')
        self.build_btn.config(state=tk.NORMAL)

    def build(self):
        if not self.config:
            self.set_status("Error: build initiated without config")
            return

        self.lock()

        q = Queue(maxsize=1024)
        output = SimpleOutput(stream=QueueStream(q))
        builder = Builder(self.config, output=output)
        self.set_status("building...")

        self.builder_task = task = Thread(target=builder.build)
        task.daemon = True
        task.start()

        def update():
            try:
                while True:
                    self.console.write(q.get_nowait())
            except Empty:
                pass
            if task.is_alive():
                self.master.after(UPDATE_INTERVAL, update)
            else:
                self.unlock()
                self.set_status("")
        update()

    def quit(self):
        if self.builder_task and self.builder_task.is_alive():
            self.builder_task.join()
            self.builder_task = None
        self.master.destroy()


def main():
    root = tk.Tk()
    gui = Roman(root)
    root.eval('tk::PlaceWindow %s center' % root.winfo_pathname(root.winfo_id()))
    root.mainloop()


if __name__ == '__main__':
    main()
