import tkinter as tk

class PauseMenu:
    def __init__(self, root, resume_callback, quit_callback):
        self.root = root
        self.resume_callback = resume_callback
        self.quit_callback = quit_callback

        self.frame = tk.Frame(root, bg="gray", bd=5)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.frame, text="Game Paused", font=("Arial", 24), bg="gray", fg="white").pack(pady=10)
        tk.Button(self.frame, text="Resume", font=("Arial", 16), command=self.resume).pack(pady=5)
        tk.Button(self.frame, text="Quit", font=("Arial", 16), command=self.quit).pack(pady=5)

        self.hide()

    def show(self):
        self.frame.lift()
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

    def hide(self):
        self.frame.place_forget()

    def resume(self):
        self.hide()
        self.resume_callback()

    def quit(self):
        self.quit_callback()
