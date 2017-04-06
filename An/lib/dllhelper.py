import ctypes, platform, os.path as Path

class DllHelper:
	__slots__ = ('clib',)

	"""
	:field __libname__: (pypath, name)
	:classmethod fnsign() -> (name, argtypes, restypes)
	    eg. (('attach', None, c_bool),)
	"""

	def __init__(self):
		if getattr(self, 'clib', None) is None:
			self._load()

	@classmethod
	def _load(cls):
		pyfile, libname = cls.__libname__

		if platform.system() == 'Windows':
			libname = ('%s_x86.dll' if platform.architecture()[0].startswith('32') else '%s.dll') % libname
		else:
			libname = '%s.so' % libname

		libpath = Path.join(Path.dirname(pyfile), libname)

		if Path.exists(libpath):
			cls.clib = ctypes.cdll.LoadLibrary(libpath)
		else:
			raise Exception("Could not load " + libpath)

		for name, arg, ret in cls.fnsign():
			fn = getattr(cls.clib, name)
			fn.argtypes = arg
			fn.restype = ret