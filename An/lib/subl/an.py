import sublime, sublime_api, extypes
import subl, subl.view as viewlib
from utils import string

class An:
	__slots__ = ('_data', 'window_id')

	def __init__(self):
		self._data = {}
		self.attachWindow(0)

	def onload(self):
		self.attachWindow(sublime_api.active_window())

	def attachWindow(self, window_id):
		self.window_id = window_id
		self._data.setdefault(window_id, {})
		self._data[self.window_id].setdefault('globals', extypes.Map())

	def set(self, view, edit=None):
		window_id = sublime_api.view_window(view.view_id)
		if self.window_id != window_id:
			self.attachWindow(sublime_api.view_window(view.view_id))

		if view == self.output:
			view = sublime.View(sublime_api.window_active_view(window_id))

		self.view = view
		self.edit = edit

	def tout(self, text=None):
		win = sublime.Window(self.window_id)
		if not self.output:
			self.output = win.create_output_panel('an')
			view = self.view or win.active_view()
			self.output.settings().set('color_scheme', view.settings().get('color_scheme'))

		if text is not None:
			self.output.run_command('set_text', {'text': extypes.astr(text)})

		win.run_command('show_panel', {'panel': 'output.an'})

	def cls(self):
		if self.output:
			view = self.output
			if view.is_in_edit():
				# 如果在output发起的exec, is_in_edit返回True, undo就不会运行
				sublime.set_timeout(self.cls, 500)
			else:
				while view.size():
					view.run_command('undo')

	def echo(self, *args, **dictArgs):
		dictArgs['file'] = self
		print(*args, **dictArgs)

	#作为print file参数
	def flush(self):
		if self.stdout:
			self.stdout.flush()

	def write(self, s):
		if self.stdout:
			self.stdout.write(s)
		elif self.output:
			self.output.run_command('append', {"characters": s})
			self.output.run_command('viewport_scrool', {"di": 4})

	# 打印错误
	def logerr(self, e):
		if not self.output:
			self.tout()
		import traceback
		self.echo(traceback.format_exc())

	def exec_(self, text):
		try:
			self.init_exec_env()
			exec(text, self.edit.__dict__)
			return True
		except Exception as e:
			self.logerr(e)
			return False

	def eval_(self, text):
		try:
			self.init_exec_env()
			self.edit.ret = eval(text, self.edit.__dict__)
			return True
		except Exception as e:
			self.logerr(e)
			return False

	def init_exec_env(self):
		edit = self.edit
		edit.an = self
		edit.view = self.view
		edit.print = self.echo
		edit._print = print
		if self.globals:
			for key, val in self.globals.items():
				edit.__dict__.setdefault(key, val)

	def open(self, file):
		"""打开文件或目录"""
		subl.open(file, sublime.Window(self.window_id))

	def popup(self, text, **args):
		self.view.show_popup('<style>body{margin:0; padding:10px; color:#ccc; font-size:18px; background-color:#000;}</style>' + text, **args);

	def __getattr__(self, name):
		return self._data[self.window_id].get(name, None)

	def __setattr__(self, name, value):
		if name in __class__.__slots__:
			object.__setattr__(self, name, value)
		else:
			self._data[self.window_id][name] = value

	def __delattr__(self, name):
		if name in __class__.__slots__:
			object.__delattr__(self, name)
		else:
			del self._data[self.window_id][name]

	def sublvars(self):
		"""sublime variables"""
		return sublime_api.window_extract_variables(self.window_id)

	def varsval(self, val):
		return sublime_api.expand_variables(val, self.sublvars())

	# 复制的数组（用换行分隔）
	# 另见: selected_text
	@property
	def copied(self):
		return sublime.get_clipboard().split('\n')

	def text(self, view=None):
		return viewlib.view_text(view or self.view)

	def selected_text(self, view=None):
		return viewlib.selected_text(view or self.view)

	def clone(self):
		self.run_win_command('clone_file')

	def matchAll(self, reg, fn):
		return string.matchAll(self.text(), reg, fn)

	def replace(self, rulers):
		result = string.replace(self.text(), rulers)
		self.view.run_command('set_text', {'text': result})

	region = staticmethod(viewlib.view_region)
	run_win_command = sublime.Window.run_command