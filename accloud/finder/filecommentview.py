import logging

import datetime
import jsonpickle
from pyramid.renderers import render
from pyramid.view import view_config

from models import DBSession
from models.FileCommentsModel import FileCommentsModel
from models.FileDescriptionModel import FileDescriptionModel
from models.FileLabelModel import FileLabelModel


class FileCommentView():

    def __init__(self, request):
        self.request = request

    def _retrieve_description(self, file):
        logger = logging.getLogger(__name__)
        db_description = DBSession.query(FileDescriptionModel.id, FileDescriptionModel.obj).filter(
            FileDescriptionModel.file == file).all()

        if len(db_description) > 0:
            try:
                description_json = db_description[-1][1]
                description_obj = jsonpickle.decode(description_json)
                description = description_obj['description']
            except BaseException as e:
                description = 'Error: {0}'.format(e.message)
                logger.error('str(e')
        else:
            description = 'No description set'
        return description

    def _retrieve_comments(self, file):
        logger = logging.getLogger(__name__)
        db_comments = DBSession.query(FileCommentsModel.id, FileCommentsModel.object).filter(
            FileCommentsModel.filename == file).all()
        comments = []
        for c in db_comments:
            try:
                tmp = jsonpickle.decode(c[1])
                comments.append(tmp)
            except BaseException as e:
                logger.warning(str(e))
        return comments

    def _retrieve_label(self, file):
        logger = logging.getLogger(__name__)
        db_label = DBSession.query(FileLabelModel.id, FileLabelModel.label).filter(
            FileLabelModel.filename == file
        ).all()
        if len(db_label) > 0:
            label = db_label[-1][1]
        else:
            label = ''
        return label


    @view_config(route_name='files_comment', permission='authenticatedusers', renderer='template/index.pt')
    def file_comment_view(self):
        file = self.request.matchdict['file']
        action = self.request.matchdict['action']
        assert (action == 'comment')
        logger = logging.getLogger(__name__)

        comments = self._retrieve_comments(file)
        description = self._retrieve_description(file)
        label = self._retrieve_label(file)

        html = render('template/filecomments.pt', dict(file=file,
                                                       description=description,
                                                       comments=comments,
                                                       label=label,
                                                       logged_in=self.request.authenticated_userid))
        return dict(files=[], folders=[], pagetitle='Test',
                    request=self.request, html=html, localsettingsfile=True, logged_in=self.request.authenticated_userid)


    @view_config(route_name='files_comment', permission='authenticatedusers', renderer='template/index.pt',
                 request_method='POST')
    def comments(self):
        log = logging.getLogger(__name__)
        file = self.request.matchdict['file']
        action = self.request.matchdict['action']
        assert (action == 'comment')
        if 'comment' in self.request.POST:
            new_comment_entry = dict(person=self.request.authenticated_userid,
                                     comment=self.request.POST['comment'],
                                     time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                     file=file)

            new_comment_str = jsonpickle.encode(new_comment_entry)

            try:
                DBSession.add(FileCommentsModel(file, new_comment_str))
                DBSession.commit()
            except BaseException as e:
                log.error(str(e))
        elif 'save_description' in self.request.POST:
            new_description_entry = dict(person=self.request.authenticated_userid,
                                         description=self.request.POST['description'],
                                         time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                         file=file)
            new_description_str = jsonpickle.encode(new_description_entry)
            try:
                DBSession.add(FileDescriptionModel(file, new_description_str, self.request.authenticated_userid))
                DBSession.commit()
            except BaseException as e:
                log.error(str(e))
        elif 'save_label' in self.request.POST:
            try:
                DBSession.add(FileLabelModel(file, self.request.POST['label']))
                DBSession.commit()
            except BaseException as e:
                log.error(e.message)
        else:
            logging.warning('Not yet implemented {0}'.format(self.request.POST))

        subreq = self.request.copy()
        subreq.method = 'GET'
        return self.request.invoke_subrequest(subreq)