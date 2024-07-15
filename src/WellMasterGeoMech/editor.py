import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import asyncio
import pandas as pd
import pint
import numpy as np
import os

class CustomEditorWindow(toga.Window):
    def __init__(self, id, title, csv_path, headers, unittypes, unitdict, target_units, datatypes, ureg, on_close_future):
        super().__init__(id=id, title=title)
        
        self.csv_path = csv_path
        self.headers = headers
        self.unittypes = unittypes
        self.unitdict = unitdict
        self.target_units = target_units
        self.datatypes = datatypes
        self.ureg = ureg
        self.on_close_future = on_close_future
        self.current_selections = {}
        
        self.initialize_dataframe()
        self.create_content()
        
    def load_csv_wrapper(self, widget):
        asyncio.create_task(self.load_csv(widget))

    def initialize_dataframe(self):
        if os.path.exists(self.csv_path):
            self.df = pd.read_csv(self.csv_path)
        else:
            self.df = pd.DataFrame(columns=self.headers)
        
        if list(self.df.columns) != self.headers:
            self.df.columns = self.headers
        
        self.current_units = {header: self.unitdict[unittype][0] for header, unittype in zip(self.headers, self.unittypes)}

    def create_content(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        
        # Create a box for all content (headers, units, and data)
        self.all_content_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # Fixed column width
        column_width = 120
        
        # Header row
        header_row = toga.Box(style=Pack(direction=ROW))
        for header in self.headers:
            header_box = toga.Box(style=Pack(direction=COLUMN, width=column_width, padding=2))
            header_label = toga.Label(
                header, 
                style=Pack(width=column_width-4, text_align='center', padding=5)
            )
            header_box.add(header_label)
            header_row.add(header_box)
        self.all_content_box.add(header_row)
        
        # Unit selection row
        unit_row = toga.Box(style=Pack(direction=ROW))
        for header, unittype in zip(self.headers, self.unittypes):
            unit_box = toga.Box(style=Pack(direction=COLUMN, width=column_width, padding=2))
            current_unit = toga.Selection(
                items=self.unitdict[unittype],
                on_change=lambda widget, header=header: self.on_current_unit_change(widget, header),
                style=Pack(width=column_width-4, padding=5)
            )
            self.current_selections[header] = current_unit
            unit_box.add(current_unit)
            unit_row.add(unit_box)
        self.all_content_box.add(unit_row)
        
        # Data display area (will be populated in update_data_display)
        self.data_box = toga.Box(style=Pack(direction=COLUMN))
        self.all_content_box.add(self.data_box)
        
        # Put all content in a scroll container
        self.scroll_container = toga.ScrollContainer(content=self.all_content_box, style=Pack(flex=1))
        main_box.add(self.scroll_container)
        
        # Button area
        button_area = toga.Box(style=Pack(direction=COLUMN))
        
        # Add/Remove row buttons
        row_buttons = toga.Box(style=Pack(direction=ROW, padding=5))
        add_row_button = toga.Button('Add Row', on_press=self.add_row, style=Pack(flex=1))
        remove_row_button = toga.Button('Remove Row', on_press=self.remove_row, style=Pack(flex=1))
        row_buttons.add(add_row_button)
        row_buttons.add(remove_row_button)
        button_area.add(row_buttons)
        
        # Load CSV and Clear Data buttons
        data_buttons = toga.Box(style=Pack(direction=ROW, padding=5))
        load_csv_button = toga.Button('Load CSV', on_press=self.load_csv_wrapper, style=Pack(flex=1))
        paste_data_button = toga.Button('Paste data', on_press=self.load_from_clipboard, style=Pack(flex=1))
        data_buttons.add(load_csv_button)
        data_buttons.add(paste_data_button)
        button_area.add(data_buttons)
        
        # Save and Cancel buttons
        action_buttons = toga.Box(style=Pack(direction=ROW, padding=5))
        save_button = toga.Button('Save', on_press=self.save, style=Pack(flex=1))
        clear_button = toga.Button('Clear', on_press=self.clear_data, style=Pack(flex=1))
        action_buttons.add(save_button)
        action_buttons.add(clear_button)
        button_area.add(action_buttons)
        
        main_box.add(button_area)
        
        self.content = main_box
        
        # Update data display after setting up the structure
        self.update_data_display()

    def update_data_display(self):
        # Clear existing data rows
        for child in list(self.data_box.children):
            self.data_box.remove(child)
        
        # Fixed column width
        column_width = 120
        
        # Create all rows at once, with a maximum of 1000 rows to prevent memory issues
        all_rows = []
        for i, row in self.df.head(100).iterrows():
            data_row = self.create_data_row(row, column_width)
            all_rows.append(data_row)
        
        # Add all rows to the data_box at once
        self.data_box.add(*all_rows)

        # If there are more than 1000 rows, inform the user
        if len(self.df) > 100:
            print(f"Warning: Only displaying first 1000 rows out of {len(self.df)} total rows.")

    def create_data_row(self, row, column_width):
        data_row = toga.Box(style=Pack(direction=ROW))
        for header in self.headers:
            data_box = toga.Box(style=Pack(direction=COLUMN, width=column_width, padding=2))
            input_box = toga.TextInput(
                value=str(row[header]), 
                style=Pack(width=column_width-4, padding=5)
            )
            data_box.add(input_box)
            data_row.add(data_box)
        return data_row
        
    def add_row(self, widget):
        new_row = {header: '' for header in self.headers}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Create and add only the new row
        new_data_row = self.create_data_row(new_row, 120)
        self.data_box.add(new_data_row)

    def remove_row(self, widget):
        if len(self.df) > 0:
            self.df = self.df.iloc[:-1]
            
            # Remove only the last row from the UI
            if self.data_box.children:
                self.data_box.remove(self.data_box.children[-1])

    def on_current_unit_change(self, widget, header):
        self.current_units[header] = widget.value

    async def load_csv(self, widget):
        try:
            file_path = await self.open_file_dialog(
                title="Select CSV file",
                multiselect=False,
                file_types=['csv']
            )
            if file_path:
                new_df = pd.read_csv(file_path)
                self.process_loaded_data(new_df, "CSV")
                await self.info_dialog("Success", "CSV file loaded successfully.")
            else:
                print("File selection was canceled.")
        except Exception as e:
            await self.error_dialog("Error", f"Failed to load CSV: {str(e)}")
            print(f"Error details: {str(e)}")
            
        
    def clear_data(self, widget):
        self.on_close_future.set_result(None)
        self.close()
    
    def load_from_clipboard(self, widget):
        asyncio.create_task(self.load_clipboard_async(widget))

    async def load_clipboard_async(self, widget):
        try:
            new_df = pd.read_clipboard(sep='\s+')
            self.process_loaded_data(new_df, "Clipboard")
            await self.info_dialog("Success", "Data loaded from clipboard successfully.")
        except Exception as e:
            await self.error_dialog("Error", f"Failed to load data from clipboard: {str(e)}")
            print(f"Error details: {str(e)}")
    
    def process_loaded_data(self, new_df, source):
        print(f"Processing {source} data...")
        print(f"{source} columns: {list(new_df.columns)}")
        print(f"Expected headers: {self.headers}")

        # Create a new dataframe with the expected columns
        processed_df = pd.DataFrame(columns=self.headers)

        # Copy data from new_df to processed_df column by column
        for i, header in enumerate(self.headers):
            if i < len(new_df.columns):
                processed_df[header] = new_df.iloc[:, i]
            else:
                processed_df[header] = ''  # Add blank column if source has fewer columns
                print(f"Added missing column: {header}")

        # If new_df has more columns than expected, print a warning
        if len(new_df.columns) > len(self.headers):
            print(f"Warning: {source} has {len(new_df.columns) - len(self.headers)} extra columns that were not loaded.")

        # Update the dataframe and display
        self.df = processed_df
        self.update_data_display()
    
    def save(self, widget):
        # Update dataframe with edited values
        for i, row_box in enumerate(self.data_box.children):
            for j, cell_box in enumerate(row_box.children):
                # The TextInput is the first (and only) child of the cell_box
                input_box = cell_box.children[0]
                self.df.iloc[i, j] = input_box.value
        
        self.df.replace('NaN', np.nan, inplace=True)
        self.df.replace("nan", np.nan, inplace=True)
        self.df.replace('', np.nan, inplace=True)
        # Perform unit conversion
        for header, current_unit, target_unit in zip(self.headers, self.current_units.values(), self.target_units):
            if current_unit != target_unit:
                try:
                    self.df[header] = self.df[header].apply(lambda x, ureg=self.ureg: ureg.Quantity(float(x), current_unit).to(target_unit).magnitude)
                except:
                    self.df[header] = np.nan
        # Cast columns to required datatypes
        for header, dtype in zip(self.headers, self.datatypes):
            try:
                self.df[header] = self.df[header].astype(dtype)
            except:
                self.df[header] = np.nan
        
        # Drop only rows where all values are NaN
        self.df.dropna(how='all', inplace=True)
        
         # Remove duplicates in the first column, keeping the first occurrence
        first_column = self.headers[0]
        self.df.drop_duplicates(subset=[first_column], keep='first', inplace=True)
        
        # Drop rows where the first column is NaN
        self.df = self.df[~(self.df[first_column].isna() | 
                    (self.df[first_column].astype(str).str.strip() == '0') | 
                    (self.df[first_column] == 0))]
        
        # Sort the dataframe based on the first column in ascending order
        self.df.sort_values(by=[first_column], inplace=True)
        
        # Save the dataframe back to the CSV file
        self.df.to_csv(self.csv_path, index=False)
        
        self.on_close_future.set_result(None)
        self.close()

    def cancel(self, widget):
        self.on_close_future.set_result(None)
        self.close()

async def custom_edit(app, csv_path, headers, unittypes, unitdict, target_units, datatypes, ureg=pint.UnitRegistry()):
    on_close_future = asyncio.Future()

    editor_window = CustomEditorWindow(
        id='data_editor',
        title='Data Editor',
        csv_path=csv_path,
        headers=headers,
        unittypes=unittypes,
        unitdict=unitdict,
        target_units=target_units,
        datatypes=datatypes,
        ureg=ureg,
        on_close_future=on_close_future
    )
    app.windows.add(editor_window)
    editor_window.show()

    await on_close_future
    # No return value, as we're overwriting the CSV in place