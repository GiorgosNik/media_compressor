import pytest
from unittest import mock
from ui.ui import CompressorApp
import os

@pytest.fixture
def app():
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
def test_show_help_message(mock_webbrowser, app, mock_messagebox):
    # Arrange
    mock_messagebox.return_value.get.return_value = "Contact Developer"
    
    # Act
    app.show_help_message()
    
    # Assert
    mock_messagebox.assert_called_once()
    mock_webbrowser.open.assert_called_once()