################################################################################
#   Project: legohdl
#   Script: gui.py
#   Author: Chase Ruskin
#   Description:
#       This script contains the class describing the settings GUI framework
#   and behavior for interacting, modifying, and saving settings.
################################################################################

import logging as log
import os
from .apparatus import Apparatus as apt
import webbrowser

import_success = True
try:
    import tkinter as tk
    from tkinter.ttk import *
    from tkinter import messagebox
except ModuleNotFoundError:
    import_success = False

class GUI:

    def __init__(self):
        '''
        Create a Tkinter object.
        '''
        if(import_success == False):
            log.error("Failed to open GUI for settings (unable to find tkinter).")
            return None

        #create dictionary to store tk variables
        self._tk_vars = dict()

        #create root window
        self._window = tk.Tk()
        #add icon
        file_path = os.path.realpath(__file__)
        head,_ = os.path.split(file_path)
        img = tk.Image("photo", file=head+'/data/icon.gif')
        self._window.tk.call('wm','iconphoto', self._window._w, img)
        #set the window size
        self._width,self._height = 800,600
        self._window.geometry(str(self.getW())+"x"+str(self.getH()))
        #constrain the window size
        self._window.wm_resizable(False, False)
        self._window.title("legoHDL settings")
        #center the window
        self._window = self.center(self._window)

        self.initFrames()
        #enter main loop
        try:
            self._window.mainloop()
        except KeyboardInterrupt:
            log.info("Exiting GUI...")
        pass

    def getW(self):
        return self._width

    def getH(self):
        return self._height

    def initFrames(self):
        #divide window into 2 sections
        #configure size for both sections
        menu_width = int(self.getW()/6)
        field_width = self.getW() - menu_width
        bar_height = int(self.getH()/10)
        field_height = self.getH() - bar_height

        #create the 3 main divisions
        menu_frame = tk.PanedWindow(self._window, width=menu_width, height=self.getH())
        self._field_frame = tk.LabelFrame(self._window, width=field_width, height=field_height, relief=tk.RAISED, padx=20, pady=20)
        bar_frame = tk.Frame(self._window, width=field_width, height=bar_height, relief=tk.SUNKEN)
        #don't resize frames to fit content
        bar_frame.grid_propagate(0)
        self._field_frame.grid_propagate(0)

        #layout all of the frames
        self._window.grid_rowconfigure(1, weight=1)
        self._window.grid_columnconfigure(0, weight=1)

        menu_frame.grid(row=1, sticky='w')
        bar_frame.grid(row=2, sticky='nsew')
        self._field_frame.grid(row=1, sticky='nse')
        self._field_frame.grid_columnconfigure(0, weight=1)
        
        # --- menu pane ---
        #configure side menu
        items = tk.StringVar(value=list(apt.SETTINGS.keys()))
        self._menu_list = tk.Listbox(self._window, listvariable=items, selectmode='single', relief=tk.RIDGE)
        #configure actions when pressing a menu item
        self._menu_list.bind('<Double-1>', self.select)
        #add to the pane
        menu_frame.add(self._menu_list)

        # --- field frame ---
        #configure field frame widgets
        self.loadFields('general')

        # --- bar frame ---
        #configure bar frame widgets
        btn_save = tk.Button(bar_frame, text='apply', command=self.save, relief=tk.RAISED)
        btn_cancel = tk.Button(bar_frame, text='cancel', command=self._window.quit, relief=tk.RAISED)
        btn_help = tk.Button(bar_frame, text='help', command=self.openDocs, relief=tk.RAISED)

        #map buttons on bar frame
        btn_help.pack(side=tk.RIGHT, padx=20, pady=16)
        btn_cancel.pack(side=tk.RIGHT, padx=0, pady=16)
        btn_save.pack(side=tk.RIGHT, padx=20, pady=16)
        pass

    def clrFieldFrame(self):
        for widgets in self._field_frame.winfo_children():
            widgets.destroy()

    def save(self):
        # :todo: transfer all gui fields/data into legohdl.cfg
        for key,sect in self._tk_vars.items():
            for name,field in sect.items():
                #save active-workspace if its a valid workspace available
                if(name == 'active-workspace' and field.get() in apt.SETTINGS['workspace'].keys()):
                    apt.SETTINGS[key][name] = field.get()
                #save refresh-rate only if its an integer being returned
                elif(name == 'refresh-rate'):
                    try:
                        apt.SETTINGS[key][name] = field.get()
                    except:
                        pass
                elif(key == 'script' or key == 'market'):
                    #load records directly from table for scripts
                    self._tk_vars[key] = {}
                    for record in self._tb.getAllValues():
                        self._tk_vars[key][record[0]] = record[1]
                    #copy dictionary back to settings
                    apt.SETTINGS[key] = self._tk_vars[key].copy()
                    #print('save dictionary values!')
                #save all others
                elif(isinstance(field, dict) == False):
                    apt.SETTINGS[key][name] = field.get()
                else:
                    if(key == 'label'):
                        #load records directly from table for recursive
                        if(self._tgl_labels.get() == 0):
                            self._tk_vars[key]['recursive'] = {}
                            for record in self._tb.getAllValues():
                                self._tk_vars[key]['recursive'][record[0]] = record[1]
                        #load records directly from table for shallow
                        else:
                            self._tk_vars[key]['shallow'] = {}
                            for record in self._tb.getAllValues():
                                self._tk_vars[key]['shallow'][record[0]] = record[1]
                        #copy dictionaries back to settings
                        apt.SETTINGS[key]['shallow'] = self._tk_vars[key]['shallow'].copy()
                        apt.SETTINGS[key]['recursive'] = self._tk_vars[key]['recursive'].copy()
                        pass
                    elif(key == 'workspace'):
                        #load records directly from table
                        self._tk_vars[key] = {}
                        apt.SETTINGS[key] = {}
                        for record in self._tb.getAllValues():
                            mkts = []
                            for m in list(record[2].split(',')):
                                if(m != ''):
                                    mkts += [m]
                            self._tk_vars[key][record[0]] = {'path' : record[1], 'market' : mkts}
                            apt.SETTINGS[key][record[0]] = self._tk_vars[key][record[0]].copy()

        apt.save()
        log.info("Settings saved.")
        pass

    def openDocs(self):
        '''
        Open the documentation website in default browser.
        '''
        webbrowser.open(apt.DOCUMENTATION_URL)

    def select(self, event):
        '''
        Based on button click, select which section to present in the fields
        area of the window.
        '''
        i = self._menu_list.curselection()
        if i != ():
            sect = self._menu_list.get(i)  
            self.loadFields(section=sect)
        pass

    def loadFields(self, section):
        #print('Loading',section+'...')
        #clear all widgets from the frame
        self.clrFieldFrame()
        #clear tk vars dictionary
        self._tk_vars = {section : {}}
        #re-write section title widget
        self._field_frame.config(text=section)        
        # always start label section with shallow labels begin displayed
        self._tgl_labels = tk.IntVar(value=1)

        # [!] load in legohdl.cfg variables

        def display_fields(field_map, i=0):
            '''
            Configure and map the appropiate widgets for the general settings
            section.
            '''
            for field,value in field_map.items():
                #skip profiles field
                if(field == 'profiles'):
                    continue
                
                #create widgets
                pady = 2
                padx = 20
                field_name_pos = 'w'
                field_value_pos = 'e'
                widg = tk.Label(self._field_frame, text=field)
                widg.grid(row=i, column=0, padx=padx, pady=pady, sticky=field_name_pos)
                
                if(isinstance(value, str) or value == None):
                    self._tk_vars[section][field] = tk.StringVar(value=apt.SETTINGS[section][field])
                    
                    #special case for 'active-workspace'
                    if(field == 'active-workspace'):
                        entry = tk.ttk.Combobox(self._field_frame, textvariable=self._tk_vars[section][field], values=list(apt.SETTINGS['workspace'].keys()))
                    else:
                        entry = tk.Entry(self._field_frame, width=40, textvariable=self._tk_vars[section][field])

                    entry.grid(row=i, column=2, columnspan=2, padx=padx, pady=pady, sticky=field_value_pos)
                    pass
                elif(isinstance(value, bool)):
                    self._tk_vars[section][field] = tk.BooleanVar(value=apt.SETTINGS[section][field])
                    
                    if(field == 'overlap-recursive'):
                        ToggleSwitch(self._field_frame, 'on', 'off', row=i, col=1, state_var=self._tk_vars[section][field], padx=padx, pady=pady)
                    elif(field == 'multi-develop'):
                        ToggleSwitch(self._field_frame, 'on', 'off', row=i, col=1, state_var=self._tk_vars[section][field], padx=padx, pady=pady)
                    pass
                elif(isinstance(value, int)):
                    self._tk_vars[section][field] = tk.IntVar(value=apt.SETTINGS[section][field])
                    
                    if(field == 'refresh-rate'):
                        wheel = tk.ttk.Spinbox(self._field_frame, from_=-1, to=1440, textvariable=self._tk_vars[section][field], wrap=True)
                        wheel.grid(row=i, column=2, columnspan=2, padx=padx, pady=pady, sticky=field_value_pos)
                    pass
                i += 1
            pass

        if(section == 'general'):
            #map widgets
            display_fields(apt.SETTINGS[section])
            pass
        elif(section == 'label'):
            #store 1-level dicionaries
            self._tk_vars[section]['shallow'] = apt.SETTINGS[section]['shallow'].copy()
           
            def loadShallowTable(event=None):
                #store recursive table
                #print(self._tb.getAllValues())
                self._tk_vars[section]['recursive'] = {}
                for record in self._tb.getAllValues():
                    self._tk_vars[section]['recursive'][record[0]] = record[1]
                #clear all records
                self._tb.clearRecords()
                #load labels from shallow list
                for key,val in self._tk_vars[section]['shallow'].items():
                    self._tb.insertRecord([key,val])

            def loadRecursiveTable(event=None):
                #store shallow label
                #print(self._tb.getAllValues())
                self._tk_vars[section]['shallow'] = {}
                for record in self._tb.getAllValues():
                    self._tk_vars[section]['shallow'][record[0]] = record[1]
                #clear all records
                self._tb.clearRecords()
                #load labels from recursive list
                for key,val in self._tk_vars[section]['recursive'].items():
                    self._tb.insertRecord([key,val])
            
            ToggleSwitch(self._field_frame, 'shallow', 'recursive', row=0, col=0, state_var=self._tgl_labels, offCmd=loadRecursiveTable, onCmd=loadShallowTable)
            #create the table object
            self._tb = Table(self._field_frame, 'Name (@)', 'File extension', row=1, col=0)
            self._tb.mapPeripherals(self._field_frame)

            #load the table elements from the settings
            loadShallowTable()
            self._tk_vars[section]['recursive'] = apt.SETTINGS[section]['recursive'].copy()
            
            pass
        elif(section == 'script'):
            self._tk_vars[section] = apt.SETTINGS[section].copy()
            #create the table object
            self._tb = Table(self._field_frame, 'alias', 'command', row=0, col=0)
            self._tb.mapPeripherals(self._field_frame)
            #load the table elements from the settings
            for key,val in self._tk_vars[section].items():
                self._tb.insertRecord([key,val])
            pass
        elif(section == 'workspace'):
            self._tk_vars[section] = apt.SETTINGS[section].copy()
            #create the table object
            self._tb = Table(self._field_frame, 'name', 'path', 'markets', row=0, col=0, rules=Table.workspaceRules)
            self._tb.mapPeripherals(self._field_frame)
            #load the table elements from the settings
            for key,val in self._tk_vars[section].items():
                fields = [key]+list(val.values())
                #convert any lists to strings seperated by commas
                for ii in range(len(fields)):
                    if isinstance(fields[ii], list):
                        str_list = ''
                        for f in fields[ii]:
                            str_list = str_list + str(f) + ','
                        fields[ii] = str_list

                self._tb.insertRecord(fields)
            pass
        elif(section == 'market'):
            self._tk_vars[section] = apt.SETTINGS[section].copy()
            #create the table object
            self._tb = Table(self._field_frame, 'name', 'remote connection', row=0, col=0, rules=Table.marketRules)
            self._tb.mapPeripherals(self._field_frame)
            #load the table elements from the settings
            for key,val in self._tk_vars[section].items():
                self._tb.insertRecord([key,val])
            pass

    def center(self, win):
        '''
        Center the tkinter window. Returns the modified tkinter object.
        '''
        #hide window
        win.attributes('-alpha', 0.0)
        #update information regarding window size and screen size
        win.update_idletasks()
        s_height,s_width = win.winfo_screenheight(),win.winfo_screenwidth()
        width,height = win.winfo_width(),win.winfo_height()
        #compute the left corner point for the window to be center
        center_x = int((s_width/2) - (width/2))
        centery_y = int((s_height/2) - (height/2))
        #set size and position
        win.geometry(str(width)+"x"+str(height)+"+"+str(center_x)+"+"+str(centery_y))
        #reveal window
        win.deiconify()
        win.update_idletasks()
        win.attributes('-alpha', 1.0)
        return win

    
    def initialized(self):
        '''
        Return true if the GUI object has a tkinter object.
        '''
        return hasattr(self, "_window")
    pass


class Table:

    def __init__(self, tk_frame, *headers, row=0, col=0, rules=None):
        '''
        Create an editable tkinter treeview object as a table containing records.
        '''
         #create a new frame for the scripts table
        tb_frame = tk.Frame(tk_frame)
        tb_frame.grid(row=row, column=col, sticky='nsew')
        self._initial_row = row
        #store the method in a variable that handles extra conditions for saving valid records
        self._rules = rules
        #tk.Label to print status of current command if necessary
        self._status = None

        scroll_y = tk.Scrollbar(tb_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = tk.Scrollbar(tb_frame, orient='horizontal')
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self._tv = tk.ttk.Treeview(tb_frame, column=tuple(headers), show='headings', xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set, selectmode='browse')
        self._tv.pack(fill='both', expand=1)

        scroll_y.config(command=self._tv.yview)
        scroll_x.config(command=self._tv.xview)

        #define columns
        self._tv.column("#0", width=0, stretch=tk.NO)
        for h in headers:
            if(h == headers[0]):
                self._tv.column(h, width=0, anchor='w')
            else:
                self._tv.column(h, anchor='w')

        #create headings
        self._tv.heading("#0", text="", anchor='center')
        
        for h in headers:
            self._tv.heading(h, text=h, anchor='w')

        self._headers = headers
        self._entries = []
        self._size = 0
        self._id_tracker = 0
        pass

    def getSize(self):
        return self._size

    def getHeaders(self):
        return self._headers

    def getEntries(self):
        return self._entries

    def assignID(self):
        #always increment id so every table element is unique
        self._id_tracker += 1
        return self._id_tracker

    def insertRecord(self, data, index=-1):
        '''
        Inserts a new record at specified index. Default is the appended to end
        of table.
        '''
        if(index == -1):
            index = self.getSize()
        self._tv.insert(parent='', index=index, iid=self.assignID(), text='', values=tuple(data))
        self._size += 1
        pass

    def replaceRecord(self, data, index):
        self._tv.item(index, text='', values=tuple(data))

    def removeRecord(self, index=-1):
        '''
        Removes a record from the specified index. Default is the last record.
        Also returns the popped value if successful.
        '''
        popped_val = None
        if(index == -1):
            index = self.getSize()-1
        if(self.getSize() > 0):
            popped_val = self.getValues(index)
            self._tv.delete(index)
            self._size -= 1
        return popped_val

    def clearRecords(self):
        self._tv.delete(*self._tv.get_children())
        self._size = 0

    def clearEntries(self):
        #clear any old values from entry boxes
        for ii in range(len(self.getEntries())):
            self.getEntries()[ii].delete(0,tk.END)

    def getValues(self, index):
        '''
        Returns the data values at the specified index from the table.
        '''
        fields = []
        for value in self._tv.item(index)['values']:
            fields += [value]
        return fields

    def getAllValues(self):
        '''
        Returns a list of data values for each index from the table.
        '''
        records = []
        for i in self._tv.get_children():
            records += [self.getValues(i)]
        return records


    def mapPeripherals(self, field_frame, editable=True):
        #create frame for buttons to go into
        button_frame = tk.Frame(field_frame)

        button_frame.grid(row=self._initial_row+2, column=0, sticky='ew', pady=2)
        #addition button
        button = tk.Button(button_frame, text=' + ', command=self.handleAppend)
        button.pack(side=tk.LEFT, anchor='w', padx=2)

        if(editable):
            #update button
            button = tk.Button(button_frame, text='update', command=self.handleUpdate)
            button.pack(side=tk.LEFT, anchor='w',padx=2)
            #edit button
            button = tk.Button(button_frame, text='edit', command=self.handleEdit)
            button.pack(side=tk.LEFT, anchor='w', padx=2)

        #delete button
        button = tk.Button(button_frame, text=' - ', command=self.handleRemove)
        button.pack(side=tk.LEFT, anchor='w', padx=2)

        self._status = tk.Label(button_frame, text='')
        self._status.pack(side=tk.RIGHT, anchor='e', padx=2)
        #divide up the entries among the frame width
        #text entries for editing
        entry_frame = tk.Frame(field_frame)
        entry_frame.grid(row=self._initial_row+1, column=0, sticky='ew')
        for ii in range(len(self.getHeaders())):
            if(ii == 0):
                self._entries.append(tk.Entry(entry_frame, text='', width=12))
                self._entries[-1].pack(side=tk.LEFT, fill='both')
            else:
                self._entries.append(tk.Entry(entry_frame, text=''))
                self._entries[-1].pack(side=tk.LEFT, fill='both', expand=1)

        #return the next availble row for the field_frame
        return self._initial_row+3

    def getAllRows(self, col, lower=True):
        '''
        This method returns a list of all the elements for a specific column.
        '''
        elements = []
        for it in (self._tv.get_children()):
            val = str(self.getValues(it)[col])
            val = val.lower() if(lower) else val
            elements += [val]
        return elements

    @classmethod
    def marketRules(cls, self, data, new):
        '''
        Extra rules for adding/updating a market record.

        Parameters
        ---
        self : table object instance using this method
        data : list of the new record
        new  : boolean if the record is trying to be appended (True) or inserted
        '''
        rename_atmpt = False
        duplicate_remote = False
        valid_remote = True

        #cannot rename a market
        if(new == False):
            rename_atmpt = (data[0].lower() not in self.getAllRows(col=0, lower=True))
            if(data[1] != ''):
                data[1] = apt.fs(data[1])  
                valid_remote = apt.isValidURL(data[1])

        #cannot have duplicate remote connections
        if(new == True and data[1] != ''):
            data[1] = apt.fs(data[1])
            duplicate_remote = (data[1].lower() in self.getAllRows(col=1, lower=True))
            #try to link to remote
            if(duplicate_remote == False):
                valid_remote = apt.isValidURL(data[1])
           
        if(valid_remote == False):
            tk.messagebox.showerror(title='Invalid Remote', message='This git remote repository does not exist.')
        elif(rename_atmpt):
            tk.messagebox.showerror(title='Failed Rename', message='A market cannot be renamed.')
        elif(duplicate_remote):
            tk.messagebox.showerror(title='Duplicate Remote', message='This market is already configured.')

        return (not rename_atmpt) and (not duplicate_remote) and valid_remote

    @classmethod
    def workspaceRules(cls, self, data, new):
        '''
        Extra rules for adding/updating a workspace record.

        Parameters
        ---
        self : table object instance using this method
        data : list of the new record
        new  : boolean if the record is trying to be appended (True) or inserted
        '''
        #must have a path
        valid_path = data[1] != ''
        rename_atmpt = False
        
        #cannot rename a workspace
        if(new == False):
            rename_atmpt = (data[0].lower() not in self.getAllRows(col=0, lower=True))
        
        if(valid_path == False):
            tk.messagebox.showerror(title='Invalid Path', message='A workspace cannot have an empty path.')
        elif(rename_atmpt):
            tk.messagebox.showerror(title='Failed Rename', message='A workspace cannot be renamed.')
        #print('workspace rules')
        return valid_path and (not rename_atmpt)

    def validEntry(self, data, new):
        data = list(data)
        all_blank = True
        duplicate = False
        extra_valid = True
        #ensure the data has some fields completed
        for d in data:
            if(d != ''):
                all_blank = False
                break
        #ensure the data is not a duplicate key
        if(new == True):
            col = 0
            elements = self.getAllRows(col=col, lower=True)
            duplicate = elements.count(data[col].lower())
        
        #define table data rules
        if(self._rules != None):
            extra_valid = self._rules(self, data, new)

        if(extra_valid == False):
            pass
        elif(all_blank):
            tk.messagebox.showerror(title='Empty Record', message='Cannot add an empty record.')
        elif(duplicate):
            tk.messagebox.showerror(title='Duplicate Key', message='A record already has that key.')
        return (not all_blank) and (not duplicate) and extra_valid

    def handleUpdate(self):
        #get what record is selected
        sel = self._tv.focus()
        if(sel == ''): return

        #get the fields from the entry boxes
        data = []
        for ii in range(len(self.getEntries())):
            data += [self.getEntries()[ii].get()]

        #define rules for updating data fields
        if(self.validEntry(data, new=False)):
            #cannot reconfigure a market's remote connection if it already is established
            if(self._rules != self.marketRules or self.getValues(sel)[1] == ''):
                #now plug into selected space
                self.replaceRecord(data, index=sel)
                self.clearEntries()
            else:
                tk.messagebox.showerror(title='Market Configured', message='This market\'s remote configuration is locked.')
        pass

    def handleAppend(self):
        #get the fields from the entry boxes
        data = []
        for ii in range(len(self.getEntries())):
            data += [self.getEntries()[ii].get()]

        if(self.validEntry(data, new=True)):
            #now add to new space at end
            self.insertRecord(data)
            self.clearEntries()
        pass

    def handleRemove(self):
        sel = self._tv.focus()
        if(sel == ''): return
        #delete the selected record
        self.removeRecord(int(sel))
        pass

    def handleEdit(self):
        sel = self._tv.focus()
        if(sel == ''): return
        #grab the data available at the selected table element
        data = self.getValues(sel)
        #clear any old values from entry boxes
        self.clearEntries()
        #ensure it is able to be edited (only for markets)
        if(self._rules != self.marketRules or data[1] == ''):
            #load the values into the entry boxes
            for ii in range(len(data)):
                self.getEntries()[ii].insert(0,str(data[ii]))
        else:
            tk.messagebox.showerror(title='Invalid Edit', message='This market cannot be edited.')
        pass

    def getTreeview(self):
        return self._tv

    pass


class ToggleSwitch:

    def __init__(self, tk_frame, on_txt, off_txt, row, col, state_var, onCmd=None, offCmd=None, padx=0, pady=0):
        self._state = state_var

        #create a new frame
        swt_frame = tk.Frame(tk_frame)
        swt_frame.grid(row=row, column=col, columnspan=10, sticky='ew', padx=padx, pady=pady)
        
        # radio buttons toggle between recursive table and shallow table  
        btn_on = tk.Radiobutton(swt_frame, indicatoron=0, text=on_txt, variable=state_var, value=1, width=8, command=onCmd)
        btn_off = tk.Radiobutton(swt_frame, indicatoron=0, text=off_txt, variable=state_var, value=0, width=8, command=offCmd)
        btn_off.pack(side=tk.RIGHT)
        btn_on.pack(side=tk.RIGHT)
        pass

    def getState(self):
        return self._state.get()

    pass