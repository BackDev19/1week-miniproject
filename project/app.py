from bson import ObjectId
from pymongo import MongoClient

import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from pymongo import MongoClient

# 조현우님
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# client = MongoClient('mongodb+srv://jhw3874:H8w9113874@cluster0.yqjacoo.mongodb.net/?retryWrites=true&w=majority')
# db = client.dbsparta_plus_week4

# 인권
client = MongoClient('mongodb+srv://test:sparta@cluster0.aaaog.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbsparta
@app.route('/main')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        App_list = list(db.App.find({}).sort("time", -1))
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        for App in App_list:
            App["_id"] = str( App["_id"] )
            App["like_count"] = db.likes.count_documents({"App_id": App["_id"]})
            App["chkLike"] = bool(db.likes.find_one({"App_id": App['_id'],
                                                     "username": user_info["username"]}))
        return render_template('index.html', user_info=user_info, App_list=App_list)

        # index > main으로 변경
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))



@app.route("/about/<name>")
def admin(name):
    return 'About %s' % name


@app.route('/')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route("/search")
def search():
    search_target = request.args.get("search_give", "")
    search_info = list(db.App.find({"title": { '$regex' : search_target }}).sort("time",-1))
    token_receive = request.cookies.get('mytoken')
    print(search_target)
    print(search_info)

    if search_info is None:
        return jsonify({'msg': "해당 게시물이 없습니다."})

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        for info in search_info :
            info["like_count"] = db.likes.count_documents({"App_id": str(info["_id"])})
            info["chkLike"] = bool(db.likes.find_one({"App_id": str(info['_id'])
                                                                , "username": user_info["username"]}))

        print(user_info)
        return render_template('/searchResult.html', search_info=search_info, user_info=user_info)
        # index > main으로 변경
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))



    # if search_info is None:
    #     return jsonify({'msg' : '데이터가 없습니다'})
    # else:



@app.route("/main")
def logintest():
    App_list = list(db.App.find({}, {'_id': False}))
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        print(user_info)
        return render_template('index.html', user_info=user_info, App_list=App_list)
        # index > main으로 변경
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/about/<int:user_id>')
def get_message(user_id):
    return 'Your ID is %d' % user_id

@app.route("/submit", methods=["POST"])
def web_write_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        title_receive = request.form['title_give']
        img_receive = request.form['img_give']
        comment_receive = request.form['comment_give']
        star_receive = request.form['star_give']
        address_receive = request.form['address_give']
        mytime = datetime.now().strftime('%Y-%m-%d %H:%M')

        doc = {
            "username": user_info["username"],
            'title': title_receive,
            'img': img_receive,
            'comment': comment_receive,
            'star': '⭐' * int(star_receive),
            'address': address_receive,
            'time': mytime
        }
        db.App.insert_one(doc)
        return jsonify({'msg': '등록완료'})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route("/submit", methods=["GET"])
def web_write_get():
    write_list = list(db.App.find({}, {'_id': False}))
    return jsonify({'orders': write_list})

# 게시글 삭제
@app.route("/delete_post", methods=["POST"])
def delete_post():
    App_id_receive = request.form['App_id_give']
    db.App.delete_one({'_id':ObjectId(App_id_receive)} )
    db.comments.delete_many({'App_id':App_id_receive} )
    db.likes.delete_many({'App_id':App_id_receive } )
    return jsonify({'msg':'삭제 완료!'})

# 댓글 삭제
@app.route("/delete_comment", methods=["POST"])
def delete_comment():
    comment_id_receive = request.form['comment_id_give']
    db.comments.delete_one({'_id': ObjectId( comment_id_receive ) } )
    return jsonify({'msg':'삭제 완료!'})


@app.route('/detail')
def home1():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        App_id_receive = request.args.get("App_id_give")
        board = db.App.find_one({'_id': ObjectId(App_id_receive)})
        comment_list = list(db.comments.find({'App_id': App_id_receive}).sort("time",-1))
        like_count = db.likes.count_documents({"App_id": App_id_receive})
        chkLike = bool(db.likes.find_one({"App_id": App_id_receive, "username": user_info["username"]}))
        return render_template('index_detail.html', comment_list=comment_list, board=board
                               , id=id, like_count=like_count, chkLike=chkLike, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route("/save-comment", methods=["POST"])
def comment_post():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})
    comment_receive = request.form['comment_give']
    App_id_receive = request.form['App_id_give']
    mytime = datetime.now().strftime('%Y-%m-%d %H:%M')
    doc = {
        'username':user_info["username"],
        'comment': comment_receive,
        'App_id':App_id_receive,
        'time':mytime
    }
    db.comments.insert_one( doc )
    return jsonify({'msg':'저장 완료!'})

# 코멘트받아오기
@app.route("/all-comment", methods=["GET"])
def comment_get():
    comment_list = list(db.comments.find({}, {'_id': False}))

    return jsonify({'comment_list': comment_list})


@app.route('/go_like_list')
def go_like_list():
    token_receive = request.cookies.get('mytoken')
    try:
        App_list = list(db.App.find({}).sort("time",-1))
        App_like_list = []

        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        for App in App_list:
            if bool(db.likes.find_one({"App_id": str(App['_id']),"username": user_info["username"]})) :
                App_like_list.append( App )

        for App_like in App_like_list:
            App_like["like_count"] = db.likes.count_documents({"App_id": str(App_like['_id'])})
            App_like["chkLike"] = bool(db.likes.find_one({"App_id": str(App_like['_id']),
                                                     "username": user_info["username"]}))
        return render_template('index_like.html', user_info=user_info, App_like_list=App_like_list)

        # index > main으로 변경
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        App_id_receive = request.form["App_id_give"]
        action_receive = request.form["action_give"]
        doc = {
            "App_id": App_id_receive,
            "username": user_info["username"]
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        # action 이후 좋아요 개수를 구한다
        count = db.likes.count_documents({"App_id": App_id_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
