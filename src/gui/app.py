"""
Tkinter GUI application for MTG Card Kingdom Order Parser.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Optional
import traceback

from ..models import Card
from ..parser import parse_cart_html
from ..excel_generator import generate_excel


class MTGOrderParserGUI:
    """Main GUI application window."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("MTG Card Kingdom Order Parser")
        self.root.geometry("1000x700")
        
        # Application state
        self.input_file: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.parsed_cards: List[Card] = []
        
        # Options
        self.use_formulas = tk.BooleanVar(value=True)
        self.verbose = tk.BooleanVar(value=False)
        
        # Build UI
        self._create_widgets()
        self._setup_layout()
        
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Preview table
        
        # === FILE SELECTION PANEL ===
        file_frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Input file
        ttk.Label(file_frame, text="Input HTML:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_entry = ttk.Entry(file_frame, width=50)
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Browse...", command=self._browse_input).grid(row=0, column=2, padx=5)
        
        # Output file
        ttk.Label(file_frame, text="Output XLSX:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(file_frame, width=50)
        self.output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Browse...", command=self._browse_output).grid(row=1, column=2, padx=5)
        
        # === OPTIONS PANEL ===
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Use formulas in Excel", 
                       variable=self.use_formulas).grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Checkbutton(options_frame, text="Verbose output", 
                       variable=self.verbose).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # === PREVIEW TABLE ===
        preview_frame = ttk.LabelFrame(main_frame, text="Card Preview", padding="10")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        
        # Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(preview_frame)
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree = ttk.Treeview(preview_frame, 
                                 columns=('qty', 'name', 'edition', 'condition', 'foil', 'price', 'total'),
                                 show='headings',
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading('qty', text='Qty')
        self.tree.heading('name', text='Card Name')
        self.tree.heading('edition', text='Edition')
        self.tree.heading('condition', text='Condition')
        self.tree.heading('foil', text='Foil')
        self.tree.heading('price', text='Price/unit')
        self.tree.heading('total', text='Total')
        
        self.tree.column('qty', width=50, anchor=tk.CENTER)
        self.tree.column('name', width=250)
        self.tree.column('edition', width=200)
        self.tree.column('condition', width=60, anchor=tk.CENTER)
        self.tree.column('foil', width=50, anchor=tk.CENTER)
        self.tree.column('price', width=80, anchor=tk.E)
        self.tree.column('total', width=80, anchor=tk.E)
        
        # === STATISTICS PANEL ===
        stats_frame = ttk.LabelFrame(main_frame, text="Order Statistics", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Stats labels
        stats_inner = ttk.Frame(stats_frame)
        stats_inner.grid(row=0, column=0, sticky=(tk.W, tk.E))
        stats_inner.columnconfigure(1, weight=1)
        stats_inner.columnconfigure(3, weight=1)
        stats_inner.columnconfigure(5, weight=1)
        
        ttk.Label(stats_inner, text="Total Cards:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_cards_label = ttk.Label(stats_inner, text="0", font=('TkDefaultFont', 10, 'bold'))
        self.total_cards_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(stats_inner, text="Total Price:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.total_price_label = ttk.Label(stats_inner, text="$0.00", font=('TkDefaultFont', 10, 'bold'))
        self.total_price_label.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(stats_inner, text="Foils:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.foil_count_label = ttk.Label(stats_inner, text="0", font=('TkDefaultFont', 10, 'bold'))
        self.foil_count_label.grid(row=0, column=5, sticky=tk.W)
        
        # === ACTION BUTTONS ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.parse_button = ttk.Button(button_frame, text="📄 Parse HTML", command=self._parse_html)
        self.parse_button.grid(row=0, column=0, padx=5)
        
        self.generate_button = ttk.Button(button_frame, text="📊 Generate Excel", 
                                          command=self._generate_excel, state=tk.DISABLED)
        self.generate_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="🗑️ Clear", command=self._clear_all).grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate', length=200)
        self.progress.grid(row=0, column=3, padx=20)
        
        # === LOG PANEL ===
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def _setup_layout(self):
        """Setup initial layout and state."""
        self._log("Welcome to MTG Card Kingdom Order Parser!")
        self._log("Select an HTML file to begin.")
        
    def _browse_input(self):
        """Open file dialog to select input HTML file."""
        filename = filedialog.askopenfilename(
            title="Select Card Kingdom Cart HTML",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        if filename:
            self.input_file = Path(filename)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, str(self.input_file))
            self._log(f"Selected input: {self.input_file.name}")
            
            # Auto-suggest output filename
            if not self.output_file:
                suggested_output = self.input_file.parent / "order.xlsx"
                self.output_file = suggested_output
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, str(self.output_file))
    
    def _browse_output(self):
        """Open file dialog to select output XLSX file."""
        filename = filedialog.asksaveasfilename(
            title="Save Excel Order As",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.output_file = Path(filename)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(self.output_file))
            self._log(f"Output file: {self.output_file.name}")
    
    def _parse_html(self):
        """Parse the HTML file and display cards in preview."""
        if not self.input_file or not self.input_file.exists():
            messagebox.showerror("Error", "Please select a valid input HTML file")
            return
        
        try:
            self._log(f"Parsing {self.input_file.name}...")
            self.progress.start()
            self.parse_button.config(state=tk.DISABLED)
            
            # Parse HTML
            html_content = self.input_file.read_text(encoding='utf-8')
            self.parsed_cards = parse_cart_html(html_content)
            
            self.progress.stop()
            self.parse_button.config(state=tk.NORMAL)
            
            if not self.parsed_cards:
                messagebox.showwarning("Warning", "No cards found in HTML file")
                self._log("⚠️ No cards found")
                return
            
            # Update preview table
            self._update_preview()
            
            # Update statistics
            self._update_statistics()
            
            # Enable generate button
            self.generate_button.config(state=tk.NORMAL)
            
            self._log(f"✓ Successfully parsed {len(self.parsed_cards)} cards")
            
        except Exception as e:
            self.progress.stop()
            self.parse_button.config(state=tk.NORMAL)
            error_msg = f"Error parsing HTML: {str(e)}"
            self._log(f"✗ {error_msg}")
            if self.verbose.get():
                self._log(traceback.format_exc())
            messagebox.showerror("Parse Error", error_msg)
    
    def _update_preview(self):
        """Update the preview table with parsed cards."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add cards to tree
        for card in self.parsed_cards:
            foil_text = "ДА" if card.is_foil else "НЕТ"
            values = (
                card.quantity,
                card.name,
                card.edition,
                card.condition,
                foil_text,
                f"${card.price_per_unit:.2f}",
                f"${card.total_price:.2f}"
            )
            self.tree.insert('', tk.END, values=values)
            
            if self.verbose.get():
                self._log(f"  {card.quantity}x {card.name} ({card.edition})")
    
    def _update_statistics(self):
        """Update statistics panel."""
        total_cards = sum(card.quantity for card in self.parsed_cards)
        total_price = sum(card.total_price for card in self.parsed_cards)
        foil_count = sum(card.quantity for card in self.parsed_cards if card.is_foil)
        
        self.total_cards_label.config(text=str(total_cards))
        self.total_price_label.config(text=f"${total_price:.2f}")
        self.foil_count_label.config(text=str(foil_count))
    
    def _generate_excel(self):
        """Generate Excel file from parsed cards."""
        if not self.parsed_cards:
            messagebox.showerror("Error", "No cards to export. Parse HTML first.")
            return
        
        if not self.output_file:
            messagebox.showerror("Error", "Please select an output file")
            return
        
        try:
            self._log(f"Generating Excel file: {self.output_file.name}...")
            self.progress.start()
            self.generate_button.config(state=tk.DISABLED)
            
            # Generate Excel
            generate_excel(
                self.parsed_cards,
                self.output_file,
                use_formulas=self.use_formulas.get()
            )
            
            self.progress.stop()
            self.generate_button.config(state=tk.NORMAL)
            
            self._log(f"✓ Excel file created successfully!")
            self._log(f"  Location: {self.output_file}")
            
            # Show success message
            result = messagebox.showinfo(
                "Success",
                f"Excel file created successfully!\n\nLocation: {self.output_file}\n\nOpen file now?",
                type=messagebox.OKCANCEL
            )
            
            if result == 'ok':
                # Open file with default application
                import os
                import platform
                if platform.system() == 'Windows':
                    os.startfile(self.output_file)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{self.output_file}"')
                else:  # Linux
                    os.system(f'xdg-open "{self.output_file}"')
                    
        except Exception as e:
            self.progress.stop()
            self.generate_button.config(state=tk.NORMAL)
            error_msg = f"Error generating Excel: {str(e)}"
            self._log(f"✗ {error_msg}")
            if self.verbose.get():
                self._log(traceback.format_exc())
            messagebox.showerror("Excel Error", error_msg)
    
    def _clear_all(self):
        """Clear all data and reset the application."""
        result = messagebox.askyesno("Clear All", "Clear all data and start over?")
        if result:
            # Clear state
            self.input_file = None
            self.output_file = None
            self.parsed_cards = []
            
            # Clear UI
            self.input_entry.delete(0, tk.END)
            self.output_entry.delete(0, tk.END)
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Reset statistics
            self.total_cards_label.config(text="0")
            self.total_price_label.config(text="$0.00")
            self.foil_count_label.config(text="0")
            
            # Disable generate button
            self.generate_button.config(state=tk.DISABLED)
            
            self._log("Cleared all data")
    
    def _log(self, message: str):
        """Add message to log panel.
        
        Args:
            message: Message to log
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = MTGOrderParserGUI(root)
    app.run()


if __name__ == '__main__':
    main()