__author__ = 'James DeVincentis <james.d@hexhost.net>'

from cif.types.base import Base


class Token(Base):

    def __init__(self, *initial_data, **kwargs):
        Base.__init__(self)

        self._acl = None
        self._description = None
        self._username = None
        self._write = 0
        self._groups = ['everyone']
        self._expires = None
        self._read = 1
        self._admin = 0
        self._revoked = 0
        self._token = self._generate_random_hash(32)
        self._validation = True

        if "validation" in kwargs:
            self._validation = False

        # Handle populating attributes from a call to __init__
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])

    @property
    def acl(self):
        return self._acl

    @acl.setter
    def acl(self, value):
        if value != self._acl:
            self._modified_fields.add('acl')
        self._acl = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value != self._description:
            self._modified_fields.add('description')
        self._description = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if value != self._username:
            self._modified_fields.add('username')
        self._username = value

    @property
    def write(self):
        return self._write

    @write.setter
    def write(self, value):
        if value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except Exception:
                    raise TypeError("Write must be a numeric value between 0 and 1")
            if not 0 <= value <= 1:
                raise TypeError("Write must be a numeric value between 0 and 1")
        if value != self._write:
            self._modified_fields.add('write')
        self._write = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        if value is not None and not isinstance(value, list):
            raise TypeError("Groups must be a list object")
        if value != self._groups:
            self._modified_fields.add('groups')
        self._groups = value

    @property
    def expires(self):
        return self._expires

    @expires.setter
    def expires(self, value):
        if value is not None and not isinstance(value, int):
            raise TypeError("Expires must be an integer or null")
        if value != self._expires:
            self._modified_fields.add('expires')
        self._expires = value

    @property
    def read(self):
        return self._read

    @read.setter
    def read(self, value):
        if value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except Exception:
                    raise TypeError("Read must be a numeric value between 0 and 1")
            if not 0 <= value <= 1:
                raise TypeError("Read must be a numeric value between 0 and 1")
        if value != self._read:
            self._modified_fields.add('read')
        self._read = value

    @property
    def admin(self):
        return self._admin

    @admin.setter
    def admin(self, value):
        if value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except Exception:
                    raise TypeError("Admin must be a numeric value between 0 and 1")
            if not 0 <= value <= 1:
                raise TypeError("Admin must be a numeric value between 0 and 1")
        if value != self._admin:
            self._modified_fields.add('admin')
        self._admin = value

    @property
    def revoked(self):
        return self._revoked

    @revoked.setter
    def revoked(self, value):
        if value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except Exception:
                    raise TypeError("Revoked must be a numeric value between 0 and 1")
            if not 0 <= value <= 1:
                raise TypeError("Revoked must be a numeric value between 0 and 1")
        if value != self._revoked:
            self._modified_fields.add('revoked')
        self._revoked = value

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def __diff__(self):
        """Generate a dict of only changed attributes from when the object was instantiated

        :return: Dict of changed attributes
        :rtype: dict
        """
        tmp = dict((name, self.__dict__["_{0}".format(name)]) for name in dir(self) if not name.startswith('_') and name != "todict" and name in self._modified_fields)
        tmp['token'] = self._token
        return tmp
