# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#
"""Tests for autosave.py"""

# Third party imports
import pytest

# Local imports
from spyder.plugins.editor.utils.autosave import (AutosaveForStack,
                                                  AutosaveForPlugin)


def test_autosave_component_set_interval(mocker):
    """Test that setting the interval does indeed change it and calls
    do_autosave if enabled."""
    mocker.patch.object(AutosaveForPlugin, 'do_autosave')
    addon = AutosaveForPlugin(None)
    addon.do_autosave.assert_not_called()
    addon.interval = 10000
    assert addon.interval == 10000
    addon.do_autosave.assert_not_called()
    addon.enabled = True
    addon.interval = 20000
    assert addon.do_autosave.called


@pytest.mark.parametrize('enabled', [False, True])
def test_autosave_component_timer_if_enabled(qtbot, mocker, enabled):
    """Test that AutosaveForPlugin calls do_autosave() on timer if enabled."""
    mocker.patch.object(AutosaveForPlugin, 'do_autosave')
    addon = AutosaveForPlugin(None)
    addon.do_autosave.assert_not_called()
    addon.interval = 100
    addon.enabled = enabled
    qtbot.wait(500)
    if enabled:
        assert addon.do_autosave.called
    else:
        addon.do_autosave.assert_not_called()


def test_autosave(mocker):
    """Test that AutosaveForStack.autosave writes the contents to the autosave
    file and updates the file_hashes."""
    mock_editor = mocker.Mock()
    mock_fileinfo = mocker.Mock(editor=mock_editor, filename='orig',
                                newly_created=False)
    mock_document = mocker.Mock(changed_since_autosave=True)
    mock_fileinfo.editor.document.return_value = mock_document
    mock_stack = mocker.Mock(data=[mock_fileinfo])
    addon = AutosaveForStack(mock_stack)
    addon.name_mapping = {'orig': 'autosave'}

    addon.autosave(0)
    mock_stack.compute_hash.assert_called_with(mock_fileinfo)
    mock_hash = mock_stack.compute_hash.return_value
    assert addon.file_hashes == {'autosave': mock_hash}


@pytest.mark.parametrize('exception', [False, True])
@pytest.mark.parametrize('errors', ['raise', 'ignore'])
def test_autosave_remove_autosave_file(mocker, exception, errors):
    """Test that AutosaveForStack.remove_autosave_file removes the autosave
    file, that an error dialog is displayed if an exception is raised,
    and that the autosave file is removed from `name_mapping` and
    `file_hashes`."""
    mock_remove = mocker.patch('os.remove')
    if exception:
        mock_remove.side_effect = EnvironmentError()
    mock_dialog = mocker.patch(
        'spyder.plugins.editor.utils.autosave.AutosaveErrorDialog')
    mock_stack = mocker.Mock()
    fileinfo = mocker.Mock()
    fileinfo.filename = 'orig'
    addon = AutosaveForStack(mock_stack)
    addon.name_mapping = {'orig': 'autosave'}
    addon.file_hashes = {'autosave': 42}

    addon.remove_autosave_file(fileinfo.filename, errors=errors)
    assert addon.name_mapping == {}
    assert addon.file_hashes == {}
    mock_remove.assert_called_with('autosave')
    assert mock_dialog.called == (exception and errors == 'raise')


@pytest.mark.parametrize('exception', [False, True])
@pytest.mark.parametrize('errors', ['raise', 'ignore'])
def test_autosave_remove_all_autosave_files(mocker, exception, errors):
    """
    Test that ``remove_all_autosave_files`` succeeds and handles errors.

    Check that AutosaveForStack.remove_all_autosave_files removes all
    autosaves and that an error dialog is displayed if an exception is raised.
    """
    mock_remove = mocker.patch('os.remove')
    if exception:
        mock_remove.side_effect = EnvironmentError()
    mock_dialog = mocker.patch(
        'spyder.plugins.editor.utils.autosave.AutosaveErrorDialog')
    mock_stack = mocker.Mock()
    addon = AutosaveForStack(mock_stack)
    addon.name_mapping = {}
    for idx in range(3):
        addon.name_mapping['orig_' + str(idx)] = 'autosave_' + str(idx)
    addon.file_hashes = mocker.MagicMock()

    addon.remove_all_autosave_files(errors=errors)
    assert addon.name_mapping == {}
    assert mock_remove.call_count == 3
    assert mock_remove.call_args_list == [
        (('autosave_' + str(idx),),) for idx in range(3)]
    assert mock_dialog.called == (exception and errors == 'raise')


if __name__ == "__main__":
    pytest.main()
