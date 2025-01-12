import pytest
from unittest import mock
from ui.ui import CompressorApp

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
    app.clear_ui = mock.Mock() 
    app.compress_media = mock.Mock()  
    app.directory = "/test/path"
    assert 1==1
    with mock.patch("ui.ui.Thread") as mock_thread, \
         mock.patch("ui.ui.ctk.CTkProgressBar") as MockProgressBar, \
         mock.patch("ui.ui.ctk.CTkLabel") as MockLabel, \
         mock.patch("ui.ui.ctk.CTkButton") as MockButton:
        
        # Mock UI elements
        mock_progress_bar = MockProgressBar.return_value
        mock_label = MockLabel.return_value
        mock_button = MockButton.return_value
        mock_thread_instance = mock_thread.return_value

        # Act
        app.setup_running_ui()

        # Assert
        app.clear_ui.assert_called_once()

        # Ensure widgets are created and packed correctly
        MockProgressBar.assert_called_once_with(app, orientation="horizontal", width=400)
        mock_progress_bar.pack.assert_called_once_with(pady=10)
        mock_progress_bar.set.assert_called_once_with(0)

        assert MockLabel.call_count == 4
        mock_label.pack.assert_any_call()

        MockButton.assert_called_once_with(app, text="Stop Compression", command=app.stop_operation)
        mock_button.pack.assert_called_once_with(pady=10)

        # Ensure compress_media starts in a new thread
        mock_thread.assert_called_once_with(target=app.compress_media, args=(app.directory,))
        mock_thread_instance.start.assert_called_once()
