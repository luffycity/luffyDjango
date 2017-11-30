from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from app01 import models
class LuffyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = None
        if request.method == 'POST':
            token = request.data.get('token')
        elif request.method == 'GET':
            token = request.query_params.get('token')
        if not token:
            return (None,None)
            # raise exceptions.AuthenticationFailed('认证失败')

        token_obj = models.Token.objects.filter(tk=token).first()

        if not token_obj:
            return (None,None)

        return (token_obj.user,token_obj)