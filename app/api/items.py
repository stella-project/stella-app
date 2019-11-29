from . import api


@api.route('/items/<string:item_id>')
def item():
    pass
