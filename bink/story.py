# pylint: disable=E1101, C0116

"""Handle Ink Story."""
import ctypes
import inspect
from bink.choices import Choices
from bink.tags import Tags
from bink import LIB, BINK_OK


def _external_reads_args(fn):
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    for parameter in signature.parameters.values():
        if parameter.kind == parameter.VAR_POSITIONAL:
            return True
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD):
            return True
    return False


class Story:
    """Story is the entry point of the Blade Ink lib."""
    def __init__(self, story_string: str):
        err_msg = ctypes.c_char_p()
        story = ctypes.c_void_p()
        ret = LIB.bink_story_new(
            ctypes.byref(story),
            story_string.encode('utf-8'),
            ctypes.byref(err_msg))
        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

        self._story = story

    def __next__(self):
        if not self.can_continue():
            raise StopIteration

        return self.cont()

    def __iter__(self):
        return self

    @property
    def choices(self):
        return self.get_current_choices()

    @property
    def tags(self):
        return self.get_current_tags()

    def can_continue(self):
        can_continue = ctypes.c_bool()
        ret = LIB.bink_story_can_continue(
            self._story, ctypes.byref(can_continue))

        if ret != BINK_OK:
            raise RuntimeError("Error in can_continue")

        return can_continue.value

    def cont(self) -> str:
        err_msg = ctypes.c_char_p()
        line = ctypes.c_char_p()
        ret = LIB.bink_story_cont(
            self._story,
            ctypes.byref(line),
            ctypes.byref(err_msg))

        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

        result = line.value.decode('utf-8')
        LIB.bink_cstring_free(line)

        return result

    def continue_maximally(self) -> str:
        err_msg = ctypes.c_char_p()
        line = ctypes.c_char_p()
        ret = LIB.bink_story_continue_maximally(
            self._story, ctypes.byref(line), ctypes.byref(err_msg))

        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

        result = line.value.decode('utf-8')
        LIB.bink_cstring_free(line)

        return result

    def get_current_choices(self) -> Choices:
        choices = ctypes.c_void_p()
        choice_count = ctypes.c_int()
        ret = LIB.bink_story_get_current_choices(
            self._story, ctypes.byref(choices), ctypes.byref(choice_count))

        if ret != BINK_OK:
            raise RuntimeError("Error getting current choices")

        choices = Choices(choices, choice_count.value)

        return choices

    def choose_choice_index(self, choice_index: int):
        """Chooses the `Choice` from the
        `currentChoices` list with the given index. Internally, this
        sets the current content path to what the
        `Choice` points to, ready to continue story evaluation."""
        err_msg = ctypes.c_char_p()
        cidx = ctypes.c_int(choice_index)
        ret = LIB.bink_story_choose_choice_index(
            self._story, cidx, ctypes.byref(err_msg))

        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

    def get_current_tags(self) -> Tags:
        tags = ctypes.c_void_p()
        tag_count = ctypes.c_int()
        ret = LIB.bink_story_get_current_tags(
            self._story, ctypes.byref(tags), ctypes.byref(tag_count))

        if ret != BINK_OK:
            raise RuntimeError("Error getting current tags")

        tags = Tags(tags, tag_count.value)

        return tags

    def choose_path_string(self, path: str):
        err_msg = ctypes.c_char_p()
        ret = LIB.bink_story_choose_path_string(
            self._story,
            path.encode('utf-8'),
            ctypes.byref(err_msg))
        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

    def save_state(self) -> str:
        """Saves the current state of the story and returns it as a string.
        The returned state can be loaded later using load_state()."""
        err_msg = ctypes.c_char_p()
        save_string = ctypes.c_char_p()
        ret = LIB.bink_story_save_state(
            self._story,
            ctypes.byref(save_string),
            ctypes.byref(err_msg))

        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

        result = save_string.value.decode('utf-8')
        LIB.bink_cstring_free(save_string)

        return result

    def load_state(self, save_state: str):
        """Loads a previously saved state into the story.
        This allows resuming the story from a saved point."""
        err_msg = ctypes.c_char_p()
        ret = LIB.bink_story_load_state(
            self._story,
            save_state.encode('utf-8'),
            ctypes.byref(err_msg))

        if ret != BINK_OK:
            err = err_msg.value.decode('utf-8')
            LIB.bink_cstring_free(err_msg)
            raise RuntimeError(err)

    def __del__(self):
        if hasattr(self, '_story'):
            LIB.bink_story_free(self._story)

    # --- Variable access ---

    def get_variable(self, name: str):
        """Get the current value of an Ink variable by name.

        Returns a Python value: str, int, float, or bool.
        """
        value = ctypes.c_void_p()
        ret = LIB.bink_var_get(
            self._story, name.encode('utf-8'), ctypes.byref(value))
        if ret != BINK_OK:
            raise RuntimeError(f"Error getting variable '{name}'")
        result = _value_to_python(value)
        LIB.bink_value_free(value)
        return result

    def set_variable(self, name: str, value):
        """Set an Ink variable to a new value."""
        ink_value = _python_to_value(value)
        ret = LIB.bink_var_set(
            self._story, name.encode('utf-8'), ink_value)
        if ret != BINK_OK:
            raise RuntimeError(f"Error setting variable '{name}'")

    # --- External functions ---

    def bind_external_function(self, func_name: str, fn):
        """Bind a Python callable as an Ink EXTERNAL function.

        The callable receives arguments as Python values (str/int/float/bool)
        and should return a Python value, or None for void functions.
        """
        from bink import EXTERNAL_FUNCTION_CB

        # Create a ctypes callback that wraps the Python function
        @EXTERNAL_FUNCTION_CB
        def _callback(fun_args, userdata):
            # Read arguments from the fun_args context. No-arg externals are common;
            # skip bink_fun_args_get because this native build reports a bogus count.
            args = []
            if _external_reads_args(fn):
                argc = LIB.bink_fun_args_count(fun_args)
                for i in range(argc):
                    arg_val = ctypes.c_void_p()
                    ret = LIB.bink_fun_args_get(
                        fun_args, i, ctypes.byref(arg_val))
                    if ret == BINK_OK:
                        args.append(_value_to_python(arg_val))
                        LIB.bink_value_free(arg_val)

            # Call the Python function
            result = fn(*args)

            # Convert return value
            if result is None:
                return ctypes.c_void_p(0).value or 0
            return _python_to_value(result) or 0

        # Store reference to prevent GC
        if not hasattr(self, '_external_callbacks'):
            self._external_callbacks = {}
        self._external_callbacks[func_name] = _callback

        ret = LIB.bink_bind_external_function(
            self._story,
            func_name.encode('utf-8'),
            _callback,
            ctypes.c_void_p(0))
        if ret != BINK_OK:
            raise RuntimeError(f"Error binding external function '{func_name}'")

    def unbind_external_function(self, func_name: str):
        """Remove a previously bound external function."""
        ret = LIB.bink_unbind_external_function(
            self._story, func_name.encode('utf-8'))
        if ret != BINK_OK:
            raise RuntimeError(f"Error unbinding external function '{func_name}'")
        if hasattr(self, '_external_callbacks'):
            self._external_callbacks.pop(func_name, None)

    # --- Variable observers ---

    def observe_variable(self, var_name: str, callback):
        """Register a callback to be called when an Ink variable changes.

        The callback receives (var_name: str, new_value).
        """
        from bink import VARIABLE_OBSERVER_CB

        @VARIABLE_OBSERVER_CB
        def _observer(c_name, new_value, userdata):
            name_str = c_name.decode('utf-8') if c_name else var_name
            val = _value_to_python(new_value) if new_value else None
            callback(name_str, val)

        if not hasattr(self, '_variable_observers'):
            self._variable_observers = {}
        self._variable_observers[var_name] = _observer

        ret = LIB.bink_observe_variable(
            self._story,
            var_name.encode('utf-8'),
            _observer,
            ctypes.c_void_p(0))
        if ret != BINK_OK:
            raise RuntimeError(f"Error observing variable '{var_name}'")


def _value_to_python(value) -> object:
    """Convert a bink_value pointer to a Python value.

    Tries string, int, float, bool in order and returns the first
    successful one. Returns None if no conversion works.
    """
    # Try string first (most common Ink type)
    s = ctypes.c_char_p()
    if LIB.bink_value_get_string(value, ctypes.byref(s)) == BINK_OK and s.value is not None:
        return s.value.decode('utf-8')

    # Try int
    i = ctypes.c_int64()
    if LIB.bink_value_get_int(value, ctypes.byref(i)) == BINK_OK:
        return i.value

    # Try float
    f = ctypes.c_double()
    if LIB.bink_value_get_float(value, ctypes.byref(f)) == BINK_OK:
        return f.value

    # Try bool
    b = ctypes.c_bool()
    if LIB.bink_value_get_bool(value, ctypes.byref(b)) == BINK_OK:
        return b.value

    return None


def _python_to_value(value) -> ctypes.c_void_p:
    """Convert a Python value to a bink_value pointer."""
    if isinstance(value, bool):
        return LIB.bink_value_new_bool(value)
    if isinstance(value, int):
        return LIB.bink_value_new_int(value)
    if isinstance(value, float):
        return LIB.bink_value_new_float(value)
    if isinstance(value, str):
        return LIB.bink_value_new_string(value.encode('utf-8'))
    raise TypeError(f"Cannot convert {type(value)} to bink value")


def story_from_file(story_file: str):
    with open(story_file, 'r', encoding='utf-8') as file:
        content = file.read()
        return Story(content)
