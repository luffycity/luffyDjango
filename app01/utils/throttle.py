from rest_framework.throttling import BaseThrottle,SimpleRateThrottle


class LuffyAnonRateThrottle(SimpleRateThrottle):

    scope = "luffy_anon"

    def allow_request(self, request, view):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        if request.user:
            return True

        # 获取当前访问用户的唯一标识
        self.key = self.get_cache_key(request, view)
        # 根据当前用户的唯一标识，获取所有访问记录
        # [1511312683.7824545, 1511312682.7824545, 1511312681.7824545]
        self.history = self.cache.get(self.key, [])
        # 获取当前时间
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success()

    def get_cache_key(self, request, view):
        return 'throttle_%(scope)s_%(ident)s' % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

class LuffyUserRateThrottle(SimpleRateThrottle):
    scope = "luffy_user"
    def allow_request(self, request, view):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        if not request.user:
            return True
        # 获取当前访问用户的唯一标识
        # 用户对所有页面
        # self.key = request.user.user
        # 用户对单页面
        self.key = request.user.user + view.__class__.__name__


        # 根据当前用户的唯一标识，获取所有访问记录
        # [1511312683.7824545, 1511312682.7824545, 1511312681.7824545]
        self.history = self.cache.get(self.key, [])
        # 获取当前时间
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success()

