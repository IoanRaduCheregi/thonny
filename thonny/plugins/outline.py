import re
import tkinter as tk
from tkinter import ttk
from thonny.globals import get_workbench

#TODO - see if there's a way to remember the previously focused tree item
#when the tree is rebuilt to avoid reparsing everything on every step
#idea: remember the focus item's name and line number, in the case of
#any change see if there's an item with the same name on the same line,
#or an item on any adjacent lines with nearly the same name (?)

#TODO - see if there's a way to select or somehow mark the line
#that contains the item that's double-clicked on

class OutlineView(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self._init_widgets()
        
        get_workbench().get_editor_notebook().bind("<<NotebookTabChanged>>", self._update_frame_contents ,True)
        get_workbench().bind("Save", self._update_frame_contents, True)
        get_workbench().bind("SaveAs", self._update_frame_contents, True)

    def _init_widgets(self):
        #init and place scrollbar
        self.vert_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        #init and place tree
        self.tree = ttk.Treeview(self, yscrollcommand=self.vert_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.vert_scrollbar['command'] = self.tree.yview

        #set single-cell frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        #init tree events
        self.tree.bind("<Double-Button-1>", self._on_double_click, "+")

        #configure the only tree column
        self.tree.column('#0', anchor=tk.W, stretch=True)
        self.tree.heading('#0', text='Item (type @ line)', anchor=tk.W)

    def _update_frame_contents(self, event=None):
        self._clear_tree()
        
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor is None:
            return
        
        root = self._parse_source(editor.get_code_view().get_content())
        for child in root[2]:
            self._add_item_to_tree('', child)
    
    def _parse_source(self, source):
        #all nodes in format (parent, node_indent, node_children, name, type, linenumber)
        root_node = (None, 0, [], None, None, None) #name, type and linenumber not needed for root
        active_node = root_node

        lineno = 0
        for line in source.split('\n'):
            lineno += 1
            m = re.match('[ ]*[\w]{1}', line)
            if m:
                indent = len(m.group(0))
                while indent <= active_node[1]:
                    active_node = active_node[0]

                t = re.match('[ ]*(?P<type>(def|class){1})[ ]+(?P<name>[\w]+)', line)
                if t:
                    current = (active_node, indent, [], t.group('name'), t.group('type'), lineno)
                    active_node[2].append(current)
                    active_node = current
        
        return root_node


    #adds a single item to the tree, recursively calls itself to add any child nodes
    def _add_item_to_tree(self, parent, item):
        #create the text to be played for this item
        item_text = item[3] + ' (' + item[4] + ' @ ' + str(item[5]) + ')'
        
        #insert the item, set lineno as a 'hidden' value
        current = self.tree.insert(parent, 'end', text=item_text, values = item[5])

        for child in item[2]:
            self._add_item_to_tree(current, child)
        
    #clears the tree by deleting all items      
    def _clear_tree(self):
        for child_id in self.tree.get_children():
            self.tree.delete(child_id)

    #called when a double-click is performed on any items
    def _on_double_click(self, event):
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor:
            code_view = editor.get_code_view() 
            lineno = self.tree.item(self.tree.focus())['values'][0]
            index = code_view.text.index(str(lineno) + '.0')
            code_view.text.see(index) #make sure that the double-clicked item is visible
            code_view.select_lines(lineno, lineno)
            
            get_workbench().event_generate("OutlineDoubleClick",
                item_text=self.tree.item(self.tree.focus(), option='text'))

def load_plugin(): 
    get_workbench().add_view(OutlineView, "Outline", "ne")
