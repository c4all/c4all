from django import template

register = template.Library()


def do_user_avatar(parser, token):
    return UserAvatarNode()


class UserAvatarNode(template.Node):
    def render(self, context):
        user = context['request'].user
        if not user.is_anonymous():
            return_value = user.avatar_num
        elif context.get('user_avatar_num', None):
            return_value = context['user_avatar_num']
        else:
            return_value = 6  # green diamond

        return "%02d.png" % return_value

register.tag('user_avatar', do_user_avatar)
