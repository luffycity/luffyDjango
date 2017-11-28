from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from app01 import models
class LuffyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        tk = request.query_params.get('tk')
        if not tk:
            return (None,None)
            # raise exceptions.AuthenticationFailed('认证失败')

        token_obj = models.Token.objects.filter(token=tk).first()
        if not token_obj:
            return (None,None)

        return (token_obj.user,token_obj)