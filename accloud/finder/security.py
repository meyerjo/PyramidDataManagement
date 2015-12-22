USERS = {'editor': 'editor',
         'viewer': 'viewer',
         'johannes': 'meyer'}
GROUPS = {'editor': ['group:editors'],
          'johannes': ['g:admin']}


def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])
