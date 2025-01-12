import pytest
from unittest import mock
from ui.ui import CompressorApp
import os

@pytest.fixture
def app():
    os.environ['TCL_LIBRARY'] = r'C:\Python312\tcl\tcl8.6'
    os.environ['TK_LIBRARY'] = r'C:\Python312\tcl\tk8.6'
    with mock.patch("ui.ui.CompressorApp.iconbitmap"):
        app = CompressorApp()
        yield app
        app.destroy()

@pytest.fixture 
def mock_messagebox():
    with mock.patch('ui.ui.CTkMessagebox') as mock_mb:
        mock_mb.return_value.get.return_value = "OK"
        yield mock_mb

@pytest.fixture
def mock_filedialog():
    with mock.patch('tkinter.filedialog.askdirectory') as mock_fd:
        yield mock_fd

def test_init(app):
    assert app.title() == "GEP Media Compressor"
    assert app.running is False
    assert app.widgets != {}
    assert app.SELECT_DIRECTORY_TEXT == "Select a directory"

def test_clear_placeholder(app):
    app.directory_string_var.set(app.SELECT_DIRECTORY_TEXT)
    app.clear_placeholder(None)
    assert app.directory_string_var.get() == ""

def test_restore_placeholder(app):
    app.directory_string_var.set("")
    app.restore_placeholder(None) 
    assert app.directory_string_var.get() == "Select a directory"

def test_select_directory(app, mock_filedialog):
    # Arrange
    mock_filedialog.return_value = "/test/path"
    
    # Act
    app.select_directory()
    
    # Assert
    assert app.directory == "/test/path"
    assert app.widgets["dir_input"].get() == "/test/path"

def test_start_application_no_directory(app, mock_messagebox):
    # Arrange
    app.directory = ""
    
    # Act
    app.start_application()
    
    # Assert 
    mock_messagebox.assert_called_once()
    assert app.running is False

def test_start_application_invalid_directory(app, mock_messagebox):
    # Arrange
    app.directory = "invalid/path"
    
    # Act
    app.start_application()
    
    # Assert
    mock_messagebox.assert_called_once()
    assert app.running is False
    
def test_start_application_valid_directory(app, mock_messagebox):
    # Arrange
    valid_directory = "/valid/test/path"
    app.directory = valid_directory
    
    with mock.patch('os.path.isdir', return_value=True):
        with mock.patch.object(app, 'setup_running_ui') as mock_setup_running_ui:
            # Act
            app.start_application()
    
    # Assert
    assert app.running is True
    mock_setup_running_ui.assert_called_once()
    mock_messagebox.assert_not_called()

def test_stop_operation(app, mock_messagebox):
    # Arrange
    app.running = True
    app.eta_updater_running = True
    
    # Act  
    app.stop_operation()
    
    # Assert
    assert app.running is False
    assert app.eta_updater_running is False
    mock_messagebox.assert_called_once()

@mock.patch('ui.ui.webbrowser')
def test_contact_developer(mock_webbrowser, app, mock_messagebox):
    # Arrange
    mock_messagebox.return_value.get.return_value = "Contact Developer"
    
    # Act
    app.show_help_message()
    
    # Assert
    mock_messagebox.assert_called_once()
    mock_webbrowser.open.assert_called_once()

@mock.patch('ui.ui.webbrowser')
def test_get_updates(mock_webbrowser, app, mock_messagebox):
    # Arrange
    mock_messagebox.return_value.get.return_value = "Get Updates"
    
    # Act
    app.show_help_message()
    
    # Assert
    mock_messagebox.assert_called_once()
    mock_webbrowser.open.assert_called_once()

@mock.patch('ui.ui.webbrowser')
def test_show_readme(mock_webbrowser, app, mock_messagebox):
    # Arrange
    mock_messagebox.return_value.get.return_value = "View README"
    
    # Act
    app.show_help_message()
    
    # Assert
    mock_messagebox.assert_called_once()
    mock_webbrowser.open.assert_called_once()

def test_clear_ui(app):
    # Arrange
    widget = mock.Mock()
    app.widgets = {'test_widget': widget}
    
    # Act
    app.clear_ui()
    
    # Assert
    widget.pack_forget.assert_called_once()

@mock.patch('ui.ui.os')
def test_open_output_directory_windows(mock_os, app):
    # Arrange  
    mock_os.name = 'nt'
    app.directory = "/test/path"
    
    # Act
    app.open_output_directory()
    
    # Assert
    mock_os.startfile.assert_called_once_with('/test/path')

def test_on_text_change(app):
    # Arrange
    app.widgets["dir_input"].insert(0, "/test/path")
    
    # Act
    app.directory_string_var.set("/test/path")
    
    # Assert
    assert app.directory == "/test/path"

def test_on_global_click_outside_input(app):
    # Arrange
    mock_event = mock.Mock()
    mock_event.widget = mock.Mock()
    app.directory_string_var.set("")
    
    # Act
    app.on_global_click(mock_event)
    
    # Assert
    assert app.directory_string_var.get() == app.SELECT_DIRECTORY_TEXT
    
def test_get_path(app):
    # Arrange
    mock_event = mock.Mock()
    mock_event.data = "{/test/path}"
    app.running = False
    
    with mock.patch('os.path.isdir', return_value=True):
        # Act
        app.get_path(mock_event)
        
        # Assert
        assert app.directory == "/test/path"
        assert app.directory_string_var.get() == "/test/path"
        

def test_setup_running_ui(app):
    # Arrange
    app.directory = "/test/path"
    with mock.patch('ui.ui.Thread') as mock_thread:
        # Act
        app.setup_running_ui()
        
        # Assert
        # Check that progress bar and labels are created
        assert "progress_bar" in app.widgets
        assert "elapsed_time_label" in app.widgets
        assert "eta_label" in app.widgets
        assert "current_file_label" in app.widgets
        assert "file_count_label" in app.widgets
        assert "stop_button" in app.widgets
        
        # Verify initial values
        assert app.widgets["elapsed_time_label"].cget("text") == "Elapsed Time: 00:00:00"  
        assert app.widgets["eta_label"].cget("text") == "ETA: --:--:--"
        assert app.widgets["current_file_label"].cget("text") == "Current File: None"
        assert app.widgets["file_count_label"].cget("text") == "Processed: 0/0"
        
        # Verify compression thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
