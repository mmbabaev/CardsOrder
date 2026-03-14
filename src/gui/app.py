"""
Tkinter GUI application for MTG Card Kingdom Order Parser.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
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
        # Colors
        bg_color = '#f0f0f0'
        frame_bg = '#ffffff'
        
        # Main container
        self.main_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === FILE SELECTION PANEL ===
        self.file_frame = tk.LabelFrame(self.main_frame, text="Files", bg=frame_bg, padx=10, pady=10)
        self.file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input file
        input_row = tk.Frame(self.file_frame, bg=frame_bg)
        input_row.pack(fill=tk.X, pady=5)
        
        self.input_label = tk.Label(input_row, text="Input HTML:", bg=frame_bg, width=12, anchor=tk.W)
        self.input_label.pack(side=tk.LEFT)
        
        self.input_entry = tk.Entry(input_row, width=50)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.input_button = tk.Button(input_row, text="Browse...", command=self._browse_input,
                                      bg='#4CAF50', fg='white')
        self.input_button.pack(side=tk.LEFT, padx=5)
        
        # Input file hint
        hint_row1 = tk.Frame(self.file_frame, bg=frame_bg)
        hint_row1.pack(fill=tk.X)
        tk.Label(hint_row1, text="↑ 1️⃣ Откройте HTML файл корзины (скачанный с сайта Card Kingdom)", 
                bg=frame_bg, fg='#666666', font=('TkDefaultFont', 9, 'italic')).pack(anchor=tk.W, padx=(15, 0))
        
        # Output file
        output_row = tk.Frame(self.file_frame, bg=frame_bg)
        output_row.pack(fill=tk.X, pady=5)
        
        self.output_label = tk.Label(output_row, text="Output XLSX:", bg=frame_bg, width=12, anchor=tk.W)
        self.output_label.pack(side=tk.LEFT)
        
        self.output_entry = tk.Entry(output_row, width=50)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.output_button = tk.Button(output_row, text="Browse...", command=self._browse_output,
                                       bg='#2196F3', fg='white')
        self.output_button.pack(side=tk.LEFT, padx=5)
        
        # Output file hint
        hint_row2 = tk.Frame(self.file_frame, bg=frame_bg)
        hint_row2.pack(fill=tk.X)
        tk.Label(hint_row2, text="↑ 2️⃣ Задайте имя для Excel файла заказа (заполняется автоматически)", 
                bg=frame_bg, fg='#666666', font=('TkDefaultFont', 9, 'italic')).pack(anchor=tk.W, padx=(15, 0))
        
        # === OPTIONS PANEL ===
        self.options_frame = tk.LabelFrame(self.main_frame, text="Options", bg=frame_bg, padx=10, pady=10)
        self.options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.formula_check = tk.Checkbutton(self.options_frame, text="Use formulas in Excel", 
                                            variable=self.use_formulas, bg=frame_bg)
        self.formula_check.pack(side=tk.LEFT, padx=10)
        
        self.verbose_check = tk.Checkbutton(self.options_frame, text="Verbose output", 
                                            variable=self.verbose, bg=frame_bg)
        self.verbose_check.pack(side=tk.LEFT, padx=10)
        
        # === PREVIEW TABLE using Canvas ===
        self.preview_frame = tk.LabelFrame(self.main_frame, text="Card Preview", bg=frame_bg, padx=10, pady=10)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create canvas with scrollbars for reliable macOS display
        canvas_container = tk.Frame(self.preview_frame, bg='white')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree_scroll_y = tk.Scrollbar(canvas_container)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_scroll_x = tk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Use Canvas for macOS compatibility
        self.tree_canvas = tk.Canvas(canvas_container,
                                     bg='white',
                                     yscrollcommand=self.tree_scroll_y.set,
                                     xscrollcommand=self.tree_scroll_x.set,
                                     highlightthickness=0)
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_scroll_y.config(command=self.tree_canvas.yview)
        self.tree_scroll_x.config(command=self.tree_canvas.xview)
        
        # Frame inside canvas to hold text
        self.tree_inner = tk.Frame(self.tree_canvas, bg='white')
        self.canvas_window = self.tree_canvas.create_window((0, 0), window=self.tree_inner, anchor='nw')
        
        # Add header labels
        header_text = f"{'Qty':>3} | {'Card Name':<35} | {'Edition':<25} | {'Cond':^4} | {'Foil':^4} | {'Price/u':>8} | {'Total':>8}"
        self.header_label = tk.Label(self.tree_inner, text=header_text, font=('Courier', 10), 
                                     bg='lightgray', fg='black', anchor='w', justify=tk.LEFT)
        self.header_label.pack(fill=tk.X)
        
        separator = tk.Label(self.tree_inner, text='-' * len(header_text), font=('Courier', 10),
                            bg='white', fg='black', anchor='w', justify=tk.LEFT)
        separator.pack(fill=tk.X)
        
        # Container for card rows
        self.cards_container = tk.Frame(self.tree_inner, bg='white')
        self.cards_container.pack(fill=tk.BOTH, expand=True)
        
        # Update scroll region
        self.tree_inner.bind('<Configure>', lambda e: self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all")))
        
        # === STATISTICS PANEL ===
        self.stats_frame = tk.LabelFrame(self.main_frame, text="Order Statistics", bg=frame_bg, padx=10, pady=10)
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_container = tk.Frame(self.stats_frame, bg=frame_bg)
        stats_container.pack(fill=tk.X)
        
        # Total Cards
        cards_frame = tk.Frame(stats_container, bg=frame_bg)
        cards_frame.pack(side=tk.LEFT, padx=10)
        self.total_cards_text = tk.Label(cards_frame, text="Total Cards:", bg=frame_bg)
        self.total_cards_text.pack(side=tk.LEFT)
        self.total_cards_label = tk.Label(cards_frame, text="0", bg=frame_bg, font=('TkDefaultFont', 10, 'bold'))
        self.total_cards_label.pack(side=tk.LEFT, padx=5)
        
        # Total Price
        price_frame = tk.Frame(stats_container, bg=frame_bg)
        price_frame.pack(side=tk.LEFT, padx=10)
        self.total_price_text = tk.Label(price_frame, text="Total Price:", bg=frame_bg)
        self.total_price_text.pack(side=tk.LEFT)
        self.total_price_label = tk.Label(price_frame, text="$0.00", bg=frame_bg, font=('TkDefaultFont', 10, 'bold'))
        self.total_price_label.pack(side=tk.LEFT, padx=5)
        
        # Foils
        foil_frame = tk.Frame(stats_container, bg=frame_bg)
        foil_frame.pack(side=tk.LEFT, padx=10)
        self.foil_count_text = tk.Label(foil_frame, text="Foils:", bg=frame_bg)
        self.foil_count_text.pack(side=tk.LEFT)
        self.foil_count_label = tk.Label(foil_frame, text="0", bg=frame_bg, font=('TkDefaultFont', 10, 'bold'))
        self.foil_count_label.pack(side=tk.LEFT, padx=5)
        
        # === ACTION BUTTONS ===
        self.button_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.parse_button = tk.Button(self.button_frame, text="📄 Parse HTML", 
                                      command=self._parse_html, width=15, bg='#4CAF50', fg='white')
        self.parse_button.pack(side=tk.LEFT, padx=5)
        
        self.generate_button = tk.Button(self.button_frame, text="📊 Generate Excel", 
                                         command=self._generate_excel, state=tk.DISABLED, width=15,
                                         bg='#2196F3', fg='white')
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(self.button_frame, text="🗑️ Clear", 
                                      command=self._clear_all, width=10)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # === LOG PANEL using Label instead of Text ===
        self.log_frame = tk.LabelFrame(self.main_frame, text="Log", bg=frame_bg, padx=10, pady=10)
        self.log_frame.pack(fill=tk.X)
        
        # Use Frame with Labels for logs (more reliable on macOS)
        log_scroll_container = tk.Frame(self.log_frame, bg='white', height=150)
        log_scroll_container.pack(fill=tk.X)
        log_scroll_container.pack_propagate(False)
        
        log_scroll = tk.Scrollbar(log_scroll_container)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_canvas = tk.Canvas(log_scroll_container, bg='white', height=150,
                                    yscrollcommand=log_scroll.set, highlightthickness=0)
        self.log_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll.config(command=self.log_canvas.yview)
        
        self.log_inner = tk.Frame(self.log_canvas, bg='white')
        self.log_canvas.create_window((0, 0), window=self.log_inner, anchor='nw')
        
        self.log_inner.bind('<Configure>', lambda e: self.log_canvas.configure(scrollregion=self.log_canvas.bbox("all")))
        
    def _setup_layout(self):
        """Setup initial layout and state."""
        self._log("Добро пожаловать в MTG Card Kingdom Order Parser!")
        self._log("")
        self._log("Инструкция по использованию:")
        self._log("1️⃣  Нажмите ЗЕЛЕНУЮ кнопку Browse → откройте HTML файл корзины")
        self._log("2️⃣  Нажмите СИНЮЮ кнопку Browse → выберите где сохранить Excel (или оставьте автоматическое имя)")
        self._log("3️⃣  Нажмите '📄 Parse HTML' → парсинг карт из HTML")
        self._log("4️⃣  Нажмите '📊 Generate Excel' → создание файла заказа")
        self._log("")
        self._log("Готов к работе!")
        
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
            messagebox.showerror("Ошибка", "Пожалуйста, выберите корректный HTML файл")
            return
        
        try:
            self._log(f"Начинаем парсинг: {self.input_file.name}")
            self._log(f"Полный путь: {self.input_file}")
            self.parse_button.config(state=tk.DISABLED)
            
            # Parse HTML - передаем путь к файлу, а не содержимое!
            self._log(f"Вызываем parse_cart_html()...")
            self.parsed_cards = parse_cart_html(str(self.input_file))
            self._log(f"parse_cart_html() вернул {len(self.parsed_cards) if self.parsed_cards else 0} карт")
            
            self.parse_button.config(state=tk.NORMAL)
            
            if not self.parsed_cards:
                messagebox.showwarning("Предупреждение", "В HTML файле не найдено карт")
                self._log("⚠️ Карты не найдены")
                return
            
            self._log(f"Найдено карт: {len(self.parsed_cards)}")
            self._log("Вызываем _update_preview()...")
            
            # Update preview table
            self._update_preview()
            
            self._log("Вызываем _update_statistics()...")
            # Update statistics
            self._update_statistics()
            
            # Enable generate button
            self.generate_button.config(state=tk.NORMAL)
            
            self._log(f"✓ Успешно распарсено {len(self.parsed_cards)} карт")
            
        except Exception as e:
            self.parse_button.config(state=tk.NORMAL)
            error_msg = f"Ошибка парсинга HTML: {str(e)}"
            self._log(f"✗ {error_msg}")
            if self.verbose.get():
                self._log(traceback.format_exc())
            messagebox.showerror("Ошибка парсинга", error_msg)
    
    def _update_preview(self):
        """Update the preview table with parsed cards."""
        self._log(f"Обновление превью: найдено {len(self.parsed_cards)} карт")
        
        # Clear existing card rows
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        # Add cards as labels
        for idx, card in enumerate(self.parsed_cards, 1):
            foil_text = "ДА" if card.is_foil else "НЕТ"
            line = f"{card.quantity:>3} | {card.name:<35.35} | {card.edition:<25.25} | {card.condition:^4} | {foil_text:^4} | ${card.price_per_unit:>7.2f} | ${card.total_price:>7.2f}"
            
            card_label = tk.Label(self.cards_container, text=line, font=('Courier', 10),
                                 bg='white' if idx % 2 == 0 else '#f9f9f9', fg='black',
                                 anchor='w', justify=tk.LEFT)
            card_label.pack(fill=tk.X)
            
            self._log(f"  Добавлена карта {idx}: {card.name}")
            
            if self.verbose.get():
                self._log(f"  {card.quantity}x {card.name} ({card.edition})")
        
        # Update scroll region
        self.tree_inner.update_idletasks()
        self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
        
        self._log(f"Превью обновлено: отображено {len(self.parsed_cards)} карт")
    
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
            messagebox.showerror("Ошибка", "Нет карт для экспорта. Сначала распарсите HTML.")
            return
        
        if not self.output_file:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите выходной файл")
            return
        
        try:
            self._log(f"Generating Excel file: {self.output_file.name}...")
            self.generate_button.config(state=tk.DISABLED)
            
            # Generate Excel
            generate_excel(
                self.parsed_cards,
                self.output_file,
                use_formulas=self.use_formulas.get()
            )
            
            self.generate_button.config(state=tk.NORMAL)
            
            self._log(f"✓ Excel файл успешно создан!")
            self._log(f"  Расположение: {self.output_file}")
            
            # Show success message
            result = messagebox.askokcancel(
                "Успех",
                f"Excel файл успешно создан!\n\nРасположение: {self.output_file}\n\nОткрыть файл сейчас?"
            )
            
            if result:
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
            self.generate_button.config(state=tk.NORMAL)
            error_msg = f"Ошибка создания Excel: {str(e)}"
            self._log(f"✗ {error_msg}")
            if self.verbose.get():
                self._log(traceback.format_exc())
            messagebox.showerror("Ошибка Excel", error_msg)
    
    def _clear_all(self):
        """Clear all data and reset the application."""
        result = messagebox.askyesno("Очистить всё", "Очистить все данные и начать заново?")
        if result:
            # Clear state
            self.input_file = None
            self.output_file = None
            self.parsed_cards = []
            
            # Clear UI
            self.input_entry.delete(0, tk.END)
            self.output_entry.delete(0, tk.END)
            
            # Clear preview
            for widget in self.cards_container.winfo_children():
                widget.destroy()
            
            # Reset statistics
            self.total_cards_label.config(text="0")
            self.total_price_label.config(text="$0.00")
            self.foil_count_label.config(text="0")
            
            # Disable generate button
            self.generate_button.config(state=tk.DISABLED)
            
            self._log("Все данные очищены")
    
    def _log(self, message: str):
        """Add message to log panel.
        
        Args:
            message: Message to log
        """
        # Add label to log panel
        log_label = tk.Label(self.log_inner, text=message, bg='white', fg='black',
                            anchor='w', justify=tk.LEFT, font=('TkDefaultFont', 9))
        log_label.pack(fill=tk.X, anchor='w')
        
        # Update scroll region
        self.log_inner.update_idletasks()
        self.log_canvas.configure(scrollregion=self.log_canvas.bbox("all"))
        self.log_canvas.yview_moveto(1.0)  # Scroll to bottom
        
        # Also print to console
        print(f"LOG: {message}")
    
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