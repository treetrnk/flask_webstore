import os
import re
from flask import Blueprint, render_template, url_for, redirect, flash, current_app, send_from_directory, request, session, jsonify
from app.main import bp
from app import db
from flask_login import login_required, current_user
#from app.auth.authenticators import permission_required, user_permission_required
from app.main.forms import (
        DeleteCommentForm, SubscribeForm,
    )
from werkzeug.utils import secure_filename
from datetime import datetime
from app.functions import log_new, log_change
from app.main.generic_views import SaveObjView, DeleteObjView
from app.auth.authenticators import group_required
from app.models import (
    User, Category,
)

@bp.route("/subscribe", methods=['GET', 'POST'])
def subscribe():
    form = SubscribeForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            existing_user.subscribed = True
        else:
            user = User(
                    email = form.email.data,
                    subscribed = True
                )
            db.session.add(user)
        db.session.commit()
        return render_template('main/subscribed.html')
    flash('Unable to subscribe. Your email address was not valid.', 'danger')
    return redirect(url_for('main.index'))

@bp.route("/settings")
@login_required
def settings():
    marketplaces = Marketplace.l_query().order_by('name').all()
    destinations = Destination.l_query().order_by('name').all()
    boxlists = Boxlist.query.order_by('name').all()
    themes = Theme.query.order_by('name').all()
    form = SetBoxlistForm()
    return render_template('main/settings.html', 
            title='Settings', 
            marketplaces=marketplaces,
            destinations=destinations,
            boxlists=boxlists,
            themes=themes,
            form=form,
            current_bl=Boxlist.query.filter_by(current=current_app.config['COMPANY']).first(),
        )

@bp.route("/submit-comment", methods=['POST'])
@group_required('fulfillment')
def submit_comment():
    form = CommentForm()
    if form.validate_on_submit():
            comment = Comment(
                    text = comment_form.comment.data,
                    user_id = current_user.id,
                    punch_id = form.punch_id.data,
                    event_id = form.event_id.data,
                )
            db.session.add(comment)
            db.session.commit()
            if form.punch_id.data:
                comment.notify(
                        edited_user=user,
                        url=url_for('punch.edit', 
                                username=user.username, 
                                punch_id=punch_id,
                            ),
                        item=f"{user.display_name_short()}'s punch card",
                    )
                log_new(comment, 'commented on a punch card')
            if form.event_id:
                comment.notify(
                        edited_user=user,
                        url=url_for('schedule.leave_edit', 
                                username=user.username, 
                                leave_id=leave_id,
                            ),
                        item=f"{user.display_name_short()}'s leave request",
                    )
                log_new(comment, 'commented on an event')
            flash('Comment added successfully!', 'success')

    return redirect(request.referer)

@bp.route("/comment/pin", methods=['POST'])
@bp.route("/comment/pin/<int:obj_id>", methods=['GET'])
@group_required('fulfillment')
def pin_comment(obj_id=None):
    if obj_id:
        comment = Comment.query.filter_by(id=obj_id).first()
    else:
        comment = Comment.query.filter_by(id=request.form.get('obj_id')).first()
    if comment:
        if comment.product_id:
            all_comments = Comment.query.filter_by(product_id = comment.product_id).all()
        elif comment.label_id:
            all_comments = Comment.query.filter_by(label_id = comment.label_id).all()
        elif comment.item_id:
            all_comments = Comment.query.filter_by(item_id = comment.item_id).all()
        for c in all_comments:
            c.pinned = False
        comment.pinned = True
        db.session.commit()
        if obj_id:
            flash('Comment pinned.', 'success')
            return redirect(request.referrer)
        return 'True'
    if obj_id:
        flash('Comment not found.', 'danger')
        return redirect(request.referrer)
    return 'Comment not found. Unable to pin.'

@bp.route("/comment/unpin", methods=['POST'])
@bp.route("/comment/unpin/<int:obj_id>", methods=['GET'])
@group_required('fulfillment')
def unpin_comment(obj_id=None):
    if obj_id:
        comment = Comment.query.filter_by(id=obj_id).first()
    else:
        comment = Comment.query.filter_by(id=request.form.get('obj_id')).first()
    if comment:
        comment.pinned = False
        db.session.commit()
        if obj_id:
            flash('Comment unpinned.', 'success')
            return redirect(request.referrer)
        return 'True'
    if obj_id:
        flash('Comment not found.', 'danger')
        return redirect(request.referrer)
    return 'Comment not found. Unable to unpin.'

@bp.route("/comment/delete", methods=['POST'])
@bp.route("/comment/delete/<int:obj_id>", methods=['GET'])
@group_required('admin')
def delete_comment(obj_id=None):
    from app.models import Comment
    if obj_id:
        comment = Comment.query.filter_by(id=obj_id).first()
        log_new(comment, 'deleted a comment')
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully.', 'success')
        return redirect(request.referrer)
    form = DeleteCommentForm()
    if form.validate_on_submit():
        comment = Comment.query.filter_by(id=form.comment_id.data).first()
        log_new(comment, 'deleted a comment')
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully.', 'success')
        return redirect(form.redirect.data)
    return redirect(url_for('main.home'))

@bp.route("/logs")
@login_required
def logs():
    main_logs = os.listdir(current_app.config['MAIN_LOG_DIR'])
    product_logs = os.listdir(current_app.config['PRODUCT_LOG_DIR'])
    scan_logs = os.listdir(current_app.config['SCAN_LOG_DIR'])

    files = {
            'main': [],
            'product': [],
            'scan': [],
        }

    def create_log_list(logs, path):
        output = []
        if logs:
            for log in sorted(logs):
                output += [{
                        'filename': log,
                        'dir': os.path.basename(os.path.normpath(path))
                    }]
        return output

    files['main'] = create_log_list(main_logs, current_app.config['MAIN_LOG_DIR'])[::-1]
    files['product'] = create_log_list(product_logs, current_app.config['PRODUCT_LOG_DIR'])
    files['scan'] = create_log_list(scan_logs, current_app.config['SCAN_LOG_DIR'])[::-1]

    current_app.logger.debug(files['scan'])

    return render_template('main/logs.html',
            title = 'Logs',
            files = files,
        )

@bp.route("/logs/<path:folder>/<string:log_name>")
@login_required
def view_log(folder, log_name):
    try: 
        f = open(current_app.config['LOG_DIR'] + folder + '/' + log_name, 'r')
        data = f.read()
        f.close()
        return render_template('main/view-log.html',
                title = 'View Log ' + log_name,
                data = data,
                log_name=log_name,
            )
    except:
        error(request.path)
    #return send_from_directory(current_app.config['LOG_DIR'] + folder, log_name)

@bp.route("/close-window")
def close_window():
    return render_template('window-close.html')

@bp.route("/logs/errors")
@login_required
#@permission_required("view-logs")
def errorlogs():
    return send_from_directory('../logs', 'flask_portal_warnings.log')

@bp.app_errorhandler(404)
def handle_404(e):
    return render_template("404-error.html", title="Page not found")

@bp.app_errorhandler(500)
def handle_500(e):
    return render_template("500-error.html", title="Internal Server Error", error=e)

@bp.route("/uploads/<string:filename>")
def uploads(filename):
    return send_from_directory('../uploads', filename)

@bp.route("/")
@bp.route("/home")
def index():
    categories = Category.query.all()
    return render_template('main/index.html', 
            page='home', 
            categories=categories,
            css='home',
            js='home.js',
        )

@bp.route("/<path:path>")
def error(path):
    return handle_404('Not Found')
