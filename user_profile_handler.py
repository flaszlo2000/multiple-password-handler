#!/usr/bin/env python3

from tkinter import *
from tkinter import messagebox
from os.path import isfile
from json import load as json_load
from shlex import quote as shlex_quote
from scripts import easydb

CONF_PATH = "./json/user_profile_handler.json"

def critical_error(obj_from, msg):
    print(f"[*] ERROR: {msg}")
    input("Please press enter to continue...")
    obj_from.kill()
    exit()

def get_safe_data(data) -> str:
    return shlex_quote(str(data))

class PasswordFrame(Frame):
    def __init__(self, parent, root, passwd_id, user_id, reminder, index_in_passwords, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.root = root
        self.root_easy_db = self.root.getEasyDb()
        self.root_commands = self.root.getCommands()

        self._passwd_id = passwd_id
        self._user_id = user_id
        self._reminder = reminder
        self._index_in_passwords = index_in_passwords
        self._func_for_code, self._data_for_code = self.getFunc()
        if self._func_for_code not in self.root_commands: raise Exception(f"{self._func_for_code} is not included in installed functions")

        self._widget_holder_dict = {} # because we use the same binding and reset feautre with every widget the program somehow have to distinguish what it have to check and set
        #> every widget makes a record in this form:
        #> id(widget): [original, holder]
        #> with this method, the whole class stays in plug-n-play state, for instance with Entry widget:
        #> if i'd like to add more Entryes, only have to do is make the widget (as always), run the bindEntry method and make a record in this.
        
        bg_color = None
        if "bg" in kwargs.keys(): bg_color = kwargs["bg"]

        self.reminder_holder = StringVar(value=self._reminder)
        self.frame_changed_holder = IntVar()
        self.func_holder = StringVar(value=self._func_for_code)

        self.changed_checkbutton = Checkbutton(self, variable=self.frame_changed_holder, bg=bg_color, highlightbackground=bg_color, state="disabled")
        self.changed_checkbutton.bind("<Button-1>", lambda event: self.resetChanges())
        self.changed_checkbutton.grid(row=0, column=0, columnspan=2, sticky="e")

        Label(self, text="Password reminder: ", bg=bg_color).grid(row=1, column=0, sticky="w", pady=3)
        self.reminder_entry = Entry(self, textvariable=self.reminder_holder, bd=0, state="disabled")
        self.bindEntry(self.reminder_entry)
        self.reminder_entry.grid(row=1, column=1, sticky="w", padx=3, pady=3)
        self._widget_holder_dict[id(self.reminder_entry)] = [self._reminder, self.reminder_holder]

        Label(self, text="Current function: ", bg=bg_color).grid(row=2, column=0, sticky="w", pady=3)
        self.func_dropdown = OptionMenu(self, self.func_holder, *self.root_commands.keys(), command=self.funcCommand)
        self.func_dropdown.config(bg=bg_color, bd=1, highlightbackground=bg_color, state="disabled")
        self.func_dropdown.bind("<Button-1>", lambda event: self.enableWidget(self.func_dropdown))
        self.func_dropdown.grid(row=2, column=1, sticky="w", padx=3, pady=3)
        self._widget_holder_dict[id(self.func_dropdown)] = [self._func_for_code, self.func_holder]
        
        if self._data_for_code is not None:
            self.data_holder = StringVar(value=self._data_for_code)

            Label(self, text="Data: ", bg=bg_color).grid(row=3, column=0, sticky="w", pady=3)
            self.data_entry = Entry(self, textvariable=self.data_holder, bd=0, state="disabled")
            self.bindEntry(self.data_entry)
            self.data_entry.grid(row=3, column=1, sticky="w", padx=3, pady=3)
            self._widget_holder_dict[id(self.data_entry)] = [self._data_for_code, self.data_holder]

    
    def getFunc(self) -> tuple:
        func = self.root_easy_db.sendCommand(f"SELECT func, data FROM specials WHERE id={get_safe_data(self._user_id)} AND passwd_id={self._passwd_id}")[0]
        return func
    
    def bindEntry(self, widget: "instance of Entry"):
        widget.bind("<KeyRelease>", lambda event: self.changeInEntry(id(widget)))
        widget.bind("<Return>", lambda event: self.saveChanges()) 
        widget.bind("<Button-1>", lambda event: self.enableWidget(widget))
        widget.bind("<FocusOut>", lambda event: self.entryLeaveFocus())
    
    def saveChanges(self):
        if self.frame_changed_holder.get() == 1:
            # if changed something
            print("save changes TODO")

    def enableWidget(self, widget):
        widget_state = widget.cget("state")

        # feature: when the user clicks on the normal widget when it opened, it have to close
        if isinstance(widget, OptionMenu):
            # FIXME: if the entry is changed the optionmenu musnt set back the changed status
            if widget_state == "normal":
                widget.event_generate("<Escape>")
                self.func_dropdown.config(state="disabled")
                return

        if widget_state == "disabled":
            widget.config(state="normal")

    def makeCheckButtonAlive(self):
        self.frame_changed_holder.set(1)
        self.changed_checkbutton.config(state="normal")

    def makeCheckButtonDisabled(self):
        self.changed_checkbutton.config(state="disabled")
        self.frame_changed_holder.set(0)

    def changeInEntry(self, widget_id):
        if self.frame_changed_holder.get() == 0:
            # if change havent happened yet
            widget_holder_list = self._widget_holder_dict.get(widget_id) # list with [original_value, holder, obj]

            if widget_holder_list[0] != widget_holder_list[1].get():
                # if have had the first change
                self.makeCheckButtonAlive()

    def getWidgetById(self, widget_id) -> object:

        # NOTE: i am lazy af, i know i should use weakref instead of this but tkinter let this method.
        for widget in self.winfo_children():
            if id(widget) == widget_id:
                return widget

    def resetChanges(self):
        if self.frame_changed_holder.get() == 1:
            # if changed something
            self.makeCheckButtonDisabled()

            # reset everything
            for widget_id, holder_list in self._widget_holder_dict.items():
                widget = self.getWidgetById(widget_id)
                widget.config(state="disabled")
                holder_list[1].set(holder_list[0])

    def entryLeaveFocus(self):
        if self.frame_changed_holder.get() == 0:
            # if didnt change anything
            self.reminder_entry.config(state="disabled")
    
    def funcCommand(self, choice):
        if choice != self._func_for_code:
            self.makeCheckButtonAlive()
            print(choice)
        else:
            self.makeCheckButtonDisabled()
            self.func_dropdown.config(state="disabled")

class PasswordContainerFrame(Frame):
    def __init__(self, parent, passwords, **kwargs):
        super().__init__(parent, **kwargs)
        self.root = parent

        self.info_label = Label(self, text="Speciális jelszavak: ", anchor="nw")
        self.info_label.pack(fill="both")

        for password in passwords:
            # TODO
            #try :
            PasswordFrame(self, self.root, *password, bd=1, relief="sunken", bg="grey").pack(padx=2, pady=5, fill="both")
            #except Exception as error:
            #    messagebox.showerror("", error)

class UserChooserFrame(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.root = parent
        self.root_easy_db = self.root.getEasyDb()
        self.user_name_holder = StringVar()

        Label(self, text="Please give the username").pack()
        user_name_entry = Entry(self, textvariable=self.user_name_holder)
        user_name_entry.bind("<Return>", lambda event: self.sendDatas())
        user_name_entry.pack()
    
    def checkUser(self, username) -> int:
        result = None
        sql_user_check_result = self.root_easy_db.sendCommand(f"SELECT id FROM users WHERE name='{get_safe_data(username)}'")
        if sql_user_check_result: result = sql_user_check_result[0][0]

        return result
    
    def getInfos(self, sql_user_id):
        sql_special_passwds = self.root_easy_db.sendCommand(f"SELECT * FROM password_specials WHERE id='{get_safe_data(sql_user_id)}'")
        # 0: passwd_id, 1: user_id, 2: reminder, 3: index in passwords
        # TODO: empty list
        self.root.createUserConfigurationPage(sql_special_passwds)

    def sendDatas(self):
        user_name = self.user_name_holder.get()
        sql_user_id = self.checkUser(user_name)
        self.user_name_holder.set("")        

        if sql_user_id is not None:
            self.getInfos(sql_user_id)
        else:
            print("This kind of user is not exist")

class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Special password handler")

        if not isfile(CONF_PATH): critical_error(self, "Config file is missing")
        with open(CONF_PATH, "r") as conf_obj:
            db_conf = json_load(conf_obj)

        self.easydb_obj = easydb.EasyDb(db_conf)
        if not self.easydb_obj.getState(): critical_error(self, "Database failure: {0}".format(*self.easydb_obj.getErrors()))

        self._commands = { "do_nothing": None,
                           "send_notification(ifttt)": None,
                           "max_use(n)": None}

        self.user_chooser_frame = UserChooserFrame(self)
        self.user_chooser_frame.pack()
            

    def getEasyDb(self) -> easydb.EasyDb:
        return self.easydb_obj
    
    def createUserConfigurationPage(self, sql_special_passwds):
        self.passwd_container = PasswordContainerFrame(self, sql_special_passwds, bd=2, relief="groove")
        self.user_chooser_frame.destroy()
        self.passwd_container.pack()

    def getCommands(self) -> dict:
        return self._commands

    def kill(self):
        self.destroy()

if __name__ == "__main__":
    main_app = App()
    main_app.mainloop()