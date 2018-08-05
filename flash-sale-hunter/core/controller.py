import base64
import MySQLdb
import json
import os
import random
import socket
import fcntl
import struct
import signal
import datetime
import mechanize
import tweepy
import markovgen
from ssdb import SSDB
from DBUtils.PersistentDB import PersistentDB
from TwitterAPI import TwitterAPI
from dateutil.relativedelta import relativedelta
from facepy import get_extended_access_token
from raven import Client
import requests
from twitter.oauth import OAuth
from requests.utils import quote
from apps.instagram.models.instagram_subs import InstagramSubs
from apps.twitter.models.access_token import AccessToken
from apps.facebook.models.access_token import AccessToken as FBAccessToken
from apps.facebook.models.facebook_subs import FacebookSubs
from apps.twitter.models.general import General
from apps.twitter.models.main.additional_robot_psychography import AdditionalRobotPsychography
from apps.twitter.models.main.application_configuration import ApplicationConfiguration
from apps.twitter.models.main.psychography_catalog import PsychographyCatalog
from apps.twitter.models.main.robot_cluster import RobotCluster
from apps.twitter.models.main.robot_fb_cluster import RobotFbCluster
from apps.twitter.models.main.robot_log import RobotLog
from apps.twitter.models.main.soldier_schedule import SoldierSchedule
from apps.twitter.models.main.user import User
from apps.twitter.models.soldier import Soldier
from apps.twitter.models.twitter.configuration import Configuration
from apps.twitter.models.main.cluster import Cluster
from apps.twitter.models.main.general_soldier import GeneralSoldier
from apps.twitter.models.robot import Robot
from apps.twitter.models.twitter_account import TwitterAccount
from apps.twitter.models.main.general_activity_log import GeneralActivityLog
from apps.twitter.models.main.robot_proxy import RobotProxy
from apps.twitter.models.main.robot_proxy_new import RobotProxyNew
from apps.twitter.models.main.proxy import Proxy
from apps.twitter.models.main.robot_fb_proxy import RobotFbProxy
from content_management.utils import Utils
from core import config, logger
from eblib.twitter.VideoTweet import VideoTweet
from helper.general import to_dict, carrot_xml_parser_v2, init_redis, init_pusher_beanstalk
from apps.twitter.models.applications import Applications
from apps.twitter.models.application_personal import ApplicationsPersonal
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from apps.twitter.models.main.words_catalog import WordsCatalog
from apps.twitter.models.main.sentences_catalog import SentencesCatalog

class Controller:
    time_range = {"y": 365, "q": 90, "m": 30, "w": 7, "t": 1}

    def __init__(self):
        self.config = config.load()
        self.sentry = Client(self.config.get("sentry", "dsn_server"))
        self.pool_isr_main = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_main', 'dbhost'),
            user=self.config.get('db_isr_main', 'dbuser'),
            passwd=self.config.get('db_isr_main', 'dbpwd'),
            db=self.config.get('db_isr_main', 'dbname'), charset='utf8')
        self.pool_isr_twitter = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_twitter', 'dbhost'),
            user=self.config.get('db_isr_twitter', 'dbuser'),
            passwd=self.config.get('db_isr_twitter', 'dbpwd'),
            db=self.config.get('db_isr_twitter', 'dbname'), charset='utf8')
        self.pool_isr_facebook = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_facebook', 'dbhost'),
            user=self.config.get('db_isr_facebook', 'dbuser'),
            passwd=self.config.get('db_isr_facebook', 'dbpwd'),
            db=self.config.get('db_isr_facebook', 'dbname'), charset='utf8')
        self.pool_isr_instagram = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_instagram', 'dbhost'),
            user=self.config.get('db_isr_instagram', 'dbuser'),
            passwd=self.config.get('db_isr_instagram', 'dbpwd'),
            db=self.config.get('db_isr_instagram', 'dbname'), charset='utf8')
        self.pool_main = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_main', 'dbhost'),
            user=self.config.get('db_isr_main', 'dbuser'),
            passwd=self.config.get('db_isr_main', 'dbpwd'),
            db=self.config.get('db_isr_main', 'dbname'), charset='utf8')
        self.pool_isr_youtube = PersistentDB(
            MySQLdb, host=self.config.get('db_isr_youtube', 'dbhost'),
            user=self.config.get('db_isr_youtube', 'dbuser'),
            passwd=self.config.get('db_isr_youtube', 'dbpwd'),
            db=self.config.get('db_isr_youtube', 'dbname'), charset='utf8')
        self.conf = self.get_configuration()
        self.redis_pointer = init_redis()
        self.redis_pointer_ipa = init_redis(db="2")
        self.ssdb = SSDB(host=self.config.get("ssdb", "server"), port=int(self.config.get("ssdb", "port")))

    def get_configuration(self):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        conf_model = ApplicationConfiguration(conn, cursor)
        configs = None
        try:
            configs = conf_model.get_configuration_arrays()
        except Exception, e:
            logger.error("Cannot load application configuration, {}".format(e))
        finally:
            cursor.close()
            conn.close()

        return configs

    def get_twitter_oauth(self, robot_id):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        at_model = AccessToken(conn, cursor)
        robot_model = Robot(conn, cursor)
        auth = None
        try:
            robot = robot_model.get_robot(robot_id, status=True).fetchone
            # token = at_model.get_token(robot["twitter_account_id"]).fetchone
            # auth = OAuth(token["access_token"], token["access_token_secret"], self.conf["twitter_consumer_key"],
            #              self.conf["twitter_consumer_secret"])

            app_personal = self.get_twitter_apps_personal(robot["twitter_account_id"])
            app_token = self.get_apps_twitter(robot["twitter_account_id"])
            if app_personal:
                auth = OAuth(app_personal['access_token'], app_personal['access_token_secret'],
                             app_personal['consumer_key'], app_personal['consumer_secret'])
            elif app_token:
                auth = OAuth(app_token['access_token'], app_token['access_token_secret'],
                             app_token['consumer_key'], app_token['consumer_secret'])
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

        return auth

    # def get_auth(self, twitter_account_id):
    #     conn = self.pool_isr_twitter.connection()
    #     cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    #     conn_main = self.pool_isr_main.connection()
    #     cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
    #
    #     access_token = AccessToken(conn, cursor)
    #     ac_model = ApplicationConfiguration(conn_main, cursor_main)
    #
    #     try:
    #         ac_data = ac_model.get_configuration_arrays()
    #
    #         if ac_data:
    #             auth = tweepy.OAuthHandler(ac_data['twitter_consumer_key'],
    #                                        ac_data['twitter_consumer_secret'])
    #         else:
    #             auth = tweepy.OAuthHandler(self.config.get("twitter_app", "consumer_key"),
    #                                        self.config.get("twitter_app", "consumer_secret"))
    #
    #         token = access_token.get_token(twitter_account_id).fetchone
    #         auth.set_access_token(token["access_token"], token["access_token_secret"])
    #         conn.commit()
    #     except Exception:
    #         raise
    #     finally:
    #         cursor.close()
    #         conn.close()
    #
    #     return auth

    def get_apps_twitter(self, twitter_account_id):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        app_model = Applications(conn, cursor)
        try:
            app_data = app_model.get_app_token(twitter_account_id)

            if app_data:
                apps = random.choice(app_data)
            else:
                process_redis_name = "generate_token:twitter:{}".format(twitter_account_id)
                if self.redis_pointer.get(process_redis_name):
                    print ("Another process is running")
                else:
                    self.redis_pointer.set(process_redis_name, "1")

                    pusher = init_pusher_beanstalk(self.config, "generate_token_twitter")
                    job_push = {"twitter_account_id": twitter_account_id, "redis_status": 1}
                    pusher.setJob(json.dumps(job_push))

                raise Exception("apps not found, twitter_account_id: {}".format(twitter_account_id))
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

        return apps

    def get_twitter_apps_personal(self, twitter_account_id,  push=True):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        app_model = ApplicationsPersonal(conn, cursor)
        robot_model = Robot(conn, cursor)
        app, apps_data = None, None
        try:
            if twitter_account_id:
                apps_data = app_model.get_app_personal(twitter_account_id=twitter_account_id, app_status='0')
            else:
                apps_data = app_model.get_app_personal(app_status='0', limit=100)

            if apps_data:
                app = random.choice(apps_data)
            elif not apps_data and twitter_account_id and push:
                robot = robot_model.get_id_from_account_id(twitter_account_id)
                process_redis_name = "generate:twitter:apps:personal:{}".format(robot['robot_id'])
                if self.redis_pointer.get(process_redis_name):
                    print ("Another process is running")
                else:
                    self.redis_pointer.set(process_redis_name, "1")

                    pusher = init_pusher_beanstalk(self.config, "generate_twitter_apps_personal")
                    job_push = {"robot_id": robot['robot_id'], "redis_status": 1}
                    pusher.setJob(json.dumps(job_push))
                logger.info("robot: {}, account {} not have personal apps.".format(robot['robot_id'],
                                                                                   twitter_account_id), True)
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

        return app

    def get_auth(self, apps):
        try:
            auth = tweepy.OAuthHandler(apps['consumer_key'],
                                       apps['consumer_secret'])

            auth.set_access_token(apps["access_token"], apps["access_token_secret"])
        except Exception:
            raise
        return auth

    def get_robot_cluster(self, c_id, result='robot_id', socmed='twitter', status=False):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        if socmed == 'twitter':
            robot_cluster = RobotCluster(conn, cursor)
        else:
            robot_cluster = RobotFbCluster(conn, cursor)
        robot_ids = []
        try:
            robot_ids = robot_cluster.get_robot_cluster(c_id, status=status)
        except Exception:
            raise
        finally:
            list_ids = []
            for id in robot_ids:
                if result in id:
                    list_ids.append(str(id[result]))
                else:
                    list_ids.append(str(id['robot_id']))
            set_robot_id = ",".join(list_ids)
            conn.close()
            cursor.close()
            return set_robot_id

    def get_robot_general(self, user_id, result='robot_id', rfm=True):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        robot_general = GeneralSoldier(conn, cursor)
        robot_ids = []
        try:
            robot_ids = robot_general.get_robot_general(user_id, robot_follow_management=rfm)
        except Exception:
            raise
        finally:
            list_ids = []
            for id in robot_ids:
                if result in id:
                    list_ids.append(str(id[result]))
                else:
                    list_ids.append(str(id['robot_id']))
            set_robot_id = ",".join(list_ids)
            conn.close()
            cursor.close()
            return set_robot_id

    def get_robot_config(self, robot_id):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        rc_model = RobotCluster(conn, cursor)
        config_model = Configuration(conn, cursor)
        result = {}
        try:
            rc_data = rc_model.get_by_robot_id(robot_id)
            if rc_data:
                cluster_id = rc_data['c_id']
                data_conf = config_model.get_configuration_arrays(cluster_id)
                if data_conf:
                    result = data_conf
        except Exception, e:
            raise
        finally:
            conn.close()
            cursor.close()

        return result

    def get_datarobot_cluster(self, robot_id):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        rc_model = RobotCluster(conn, cursor)
        cluster_model = Cluster(conn, cursor)

        result = {}
        try:
            rc_data = rc_model.get_by_robot_id(robot_id)
            if rc_data:
                cluster_id = rc_data['c_id']
                cluster = cluster_model.get_cluster(cluster_id).fetchone
                if cluster:
                    result = cluster
        except Exception, e:
            raise
        finally:
            conn.close()
            cursor.close()

        return result

    def get_robot_twitter_id(self, age=None, gender=None, religion=None, c_id=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        twitter_account = TwitterAccount(conn, cursor)
        try:
            account_id = ""
            robot_cluster = self.get_robot_cluster(c_id=c_id)
            if robot_cluster and robot_cluster != '':
                robots = twitter_account.get_twitter_account(age=age, gender=gender, religion=religion,
                                                             robot_ids=robot_cluster)
                account_id = " OR ".join([str(robot['twitter_account_id']) for robot in robots])
        except Exception, e:
            logger.error(e)
            raise
        finally:
            conn.close()
            cursor.close()

        return account_id

    def get_soldier_by_robot_ids(self, robot_ids=None, result='soldier_id'):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        soldier_model = Soldier(conn, cursor)
        soldier_ids = []
        try:
            soldier_ids = soldier_model.get_soldier(robot_ids=robot_ids).fetchall
        except Exception:
            raise
        finally:
            list_ids = []
            for id in soldier_ids:
                if result in id:
                    list_ids.append(str(id[result]))
                else:
                    list_ids.append(str(id['soldier_id']))
            set_soldier_id = ",".join(list_ids)
            conn.close()
            cursor.close()
            return set_soldier_id

    def find_between(self, s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def search_account(self, apps, keyword, proxy_url=None):
        result = None
        try:
            list_user = list()
            attributes = ["id", "verified", "profile_image_url_https", "entities", "followers_count", "id_str",
                          "statuses_count", "description", "friends_count", "location", "profile_image_url",
                          "following",
                          "screen_name", "lang", "favourites_count", "name", "url", "created_at", "protected",
                          "time_zone",
                          "age", "gender", "religion", "country", "province", "city", "subdistrict", "village"]

            if proxy_url:
                api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            else:
                api = tweepy.API(auth_handler=self.get_auth(apps))

            data_user = api.search_users(keyword)
            if data_user:
                user_tmp = data_user._json
                user = dict()
                for attr, value in user_tmp.iteritems():
                    if attr in attributes:
                        user[attr] = value
                list_user.append(user)

            if list_user:
                result = list_user
        except Exception as e:
            print e
        finally:
            return result

    def get_followers_twitter(self, twitter_account_id, user_id=None, proxy=None):
        result = []
        try:
            if not user_id:
                user_id = twitter_account_id

            apps_personal = self.get_twitter_apps_personal(twitter_account_id)
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(twitter_account_id)

            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            result_tweet = to_dict(api.followers_ids(user_id=user_id))
            if isinstance(result_tweet, (list, tuple)):
                result = result_tweet

        except Exception, e:
            print e

        return result

    def following_user(self, twitter_account_id, user_id, proxy=None):
        try:
            apps_personal = self.get_twitter_apps_personal(twitter_account_id)
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(twitter_account_id)

            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            result_tweet = to_dict(api.create_friendship(user_id=user_id))
        except Exception, e:
            raise

    def unfollowing_user(self, twitter_account_id, user_id, proxy=None):
        result = 'success'
        try:
            apps_personal = self.get_twitter_apps_personal(twitter_account_id)
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(twitter_account_id)

            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            result_tweet = to_dict(api.destroy_friendship(user_id=user_id))
        except Exception, e:
            # raise
            result = "Failed. Account {} Error {}".format(twitter_account_id, e)
            logger.info("Account {} Error {}".format(twitter_account_id, e), True)

        return result

    def get_ip_address(self, custom_socket=None):
        list_socket = ["enp3s0f0", "wlp9s0", "eth0", "eth1", "eth2", "wlan0",
                       "eno2", "eno1", "em1", "em2", "em3", "em4", "ens160"]
    
        if custom_socket:
            list_socket = custom_socket

        ip_address = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for net_inf in list_socket:
            try:
                ip_address = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', net_inf[:15]))[20:24])
            except Exception, e:
                # print e
                pass
        return ip_address

    def error_logging(self, message, config_load=None):
        logger.error(message, sentry=self.sentry, config_load=config_load)

    def get_robot_list(self, index='twitter_account_id', order_by="name ASC", robot_ids=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = Robot(conn, cursor)
            robot_ids = [str(r[index]) for r in robot_model.get_robot(status=1, order_by=order_by,
                                                                      robot_ids=robot_ids).fetchall]
            return robot_ids
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def get_last_robot(self, _type='single', index='robot_id', max_id=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = Robot(conn, cursor)
            if _type == 'single':
                robot = robot_model.get_robot(status=1, order_by="robot_id desc").fetchone
                robot_id = robot[index]
            elif _type == 'count':
                robot_id = robot_model.get_robot(status=1).rowscount
            else:
                robots = robot_model.get_robot(status=1, order_by="robot_id desc", max_id=max_id).fetchall
                robot_id = [str(r[index]) for r in robots]

            return robot_id
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def monkeypatch_mechanize():
        """Work-around for a mechanize 0.2.5 bug. See: https://github.com/jjlee/mechanize/pull/58"""
        import mechanize
        if mechanize.__version__ < (0, 2, 6):
            from mechanize._form import SubmitControl, ScalarControl

            def __init__(self, type, name, attrs, index=None):
                ScalarControl.__init__(self, type, name, attrs, index)
                # IE5 defaults SUBMIT value to "Submit Query"; Firebird 0.6 leaves it
                # blank, Konqueror 3.1 defaults to "Submit".  HTML spec. doesn't seem
                # to define this.
                if self.value is None:
                    if self.disabled:
                        self.disabled = False
                        self.value = ""
                        self.disabled = True
                    else:
                        self.value = ""
                self.readonly = True

            SubmitControl.__init__ = __init__

    def set_screen_name(self, robot_id, screen_name, second_try=False, proxy=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        robot_model = Robot(conn, cursor)
        try:
            self.monkeypatch_mechanize()
            robot = robot_model.get_robot(robot_id=robot_id).fetchone
            if robot:
                if robot['password']:
                    if 'screen_name' in robot and robot['screen_name']:
                        screen_name_db = robot['screen_name']
                    else:
                        screen_name_db = robot['email']

                    password_db = robot['password']

                    url = 'https://mobile.twitter.com/login'
                    br = mechanize.Browser()
                    br.set_handle_robots(False)  # ignore robots
                    br.set_handle_refresh(False)  # can sometimes hang without this
                    br.addheaders = [('User-agent', 'Firefox')]  # [('User-agent', 'Firefox')]

                    br.open(url)

                    br.form = list(br.forms())[0]
                    control_username = br.form.find_control("session[username_or_email]")
                    control_password = br.form.find_control("session[password]")

                    control_username.value = screen_name_db
                    control_password.value = password_db

                    br.submit()

                    if "login/error" in br.geturl():
                        br.open(url)

                        br.form = list(br.forms())[0]
                        control_username = br.form.find_control("session[username_or_email]")
                        control_password = br.form.find_control("session[password]")

                        control_username.value = robot['email']
                        control_password.value = password_db

                        br.submit()

                    url_setting = 'https://twitter.com/settings/account'
                    br.open(url_setting)

                    br.form = list(br.forms())[2]

                    current_url = br.geturl()

                    if not second_try:
                        if "challenge_type=RetypePhoneNumber" in current_url:
                            if 'phone_no' in robot and robot['phone_no']:
                                logger.info("Retype Number robot {}".format(robot['robot_id']), True)

                                br.form = list(br.forms())[0]
                                control_challange = br.form.find_control("challenge_response")
                                control_challange.value = robot['phone_no']
                                br.submit()

                                return self.set_screen_name(robot_id, screen_name, second_try=True)
                            else:
                                logger.info("Retype Number but robot {} dont have phone no".format(robot['robot_id']), True)

                        elif "challenge_type=RetypeEmail" in current_url:
                            if 'email' in robot and robot['email']:
                                logger.info("Retype Email robot {}".format(robot['robot_id']), True)
                                br.form = list(br.forms())[0]
                                control_challange = br.form.find_control("challenge_response")
                                control_challange.value = robot['email']
                                br.submit()

                                return self.set_screen_name(robot_id, screen_name, second_try=True)
                            else:
                                logger.info("Retype Email but robot {} dont have email".format(robot['robot_id']), True)

                    if current_url == 'https://twitter.com/settings/account':
                        control_username = br.form.find_control("user[screen_name]")
                        control_password = br.form.find_control("auth_password")
                        control_username.value = screen_name
                        control_password.value = password_db

                        response = br.submit()
                        result = response.read()
                        message = self.find_between(result, '<div id="settings-alert-box" class="alert">', "</div>")
                        message = self.find_between(message, '<h4>', "</h4>")
                        message = message.strip()

                        success_list = [
                            'Terima kasih, pengaturan Anda telah disimpan.',
                            'Thanks, your settings have been saved.'
                        ]

                        if message not in success_list:
                            str_div = '<input id="user_screen_name" maxlength="15" name="user[screen_name]" ' \
                                      'type="text" value="'
                            screen_name_now = self.find_between(result, str_div, '">')
                            if screen_name_now != screen_name:
                                if not message or message == '':
                                    message = "Screen name already exist. Please change your screen name!"
                                raise Exception(message)
                    else:
                        raise Exception("Username not found, Current URL : {}".format(current_url))
                else:
                    raise Exception('Password Null')

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def get_psychography_catalog(self):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        pc_model = PsychographyCatalog(conn, cursor)
        try:
            catalog = pc_model.get_psychographycal_catalog().fetchall
            conn.commit()
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

        return catalog

    def post_retweet(self, twitter_account_id, tweet_id, apps, proxy=None):
        try:
            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            tweet = api.get_status(tweet_id)
            tweet_text = tweet.text
            screen_name = tweet.author._json['screen_name']
            updated_tweet = "RT @{}: {}".format(screen_name, tweet_text.encode('utf-8'))
            result_tweet = to_dict(api.retweet(id=tweet_id))
            result_tweet['text'] = updated_tweet
            return result_tweet
        except:
            raise

    def post_like(self, twitter_account_id, tweet_id, apps, proxy=None):
        try:
            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))
            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            result_tweet = to_dict(api.create_favorite(tweet_id))
            return result_tweet
        except Exception, e:
            raise e

    # === start additional code from dhamar ===
    def post_quote_retweet(self, twitter_account_id, tweet_id, quote_content, proxy=None):
        try:
            apps_personal = self.get_twitter_apps_personal(twitter_account_id)
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(twitter_account_id)

            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            # get detail tweet
            tweet = api.get_status(id=tweet_id)
            screen_name = tweet.user.screen_name
            id = tweet.id
            # post quote retweet
            result_tweet = to_dict(api.update_status(status="{} https://twitter.com/{}/status/{}".format(
                quote_content, screen_name, id)))
            return result_tweet
        except:
            raise
    # === end additional code from dhamar ===

    def post_tweepy(self, twitter_account_id, tweet, apps, proxy=None):
        try:
            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))
            api = tweepy.API(auth_handler=self.get_auth(apps), proxy=proxy_url)
            result_tweet = to_dict(api.update_status(status=tweet))
            return result_tweet
        except Exception, e:
            raise

    def check_status(self, r):
        if r.status_code < 200 or r.status_code > 299:
            logger.error("Status code {}, error {}".format(r.status_code, r.text))
            raise Exception(r.text)

    def tw_post_video(self, twitter_account_id, tweet, video_path):
        try:
            apps_personal = self.get_twitter_apps_personal(twitter_account_id)
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(twitter_account_id)

            auth = self.get_auth(apps)
            api = TwitterAPI(auth.consumer_key, auth.consumer_secret, auth.access_token, auth.access_token_secret)

            bytes_sent = 0
            total_bytes = os.path.getsize(video_path)
            _file = open(video_path, 'rb')
            r = api.request('media/upload', {'command': 'INIT', 'media_type': 'video/mp4', 'total_bytes': total_bytes})
            self.check_status(r)
            media_id = r.json()['media_id']
            segment_id = 0
            while bytes_sent < total_bytes:
                chunk = _file.read(4 * 1024 * 1024)
                r = api.request('media/upload',
                                {'command': 'APPEND', 'media_id': media_id, 'segment_index': segment_id},
                                {'media': chunk})
                self.check_status(r)
                segment_id += 1
                bytes_sent = _file.tell()
                info = "[Total : {}] => Sent {}".format(total_bytes, bytes_sent)
                logger.info(info, True)

            r = api.request('media/upload', {'command': 'FINALIZE', 'media_id': media_id})
            self.check_status(r)
            r = api.request('statuses/update', {'status': tweet, 'media_ids': media_id})
            self.check_status(r)
            return json.loads(r.text)
        except:
            raise

    def tw_post_video_async(self, twitter_account_id, tweet, video_path, apps, proxy=None):
        try:
            auth = self.get_auth(apps)

            proxy_url = None
            if proxy:
                proxy_url = "{}://".format(str(proxy['proxy_protocol']))
                if proxy['proxy_username'] and proxy['proxy_password']:
                    proxy_url += '{}:{}@'.format(str(proxy['proxy_username']), str(proxy['proxy_password']))
                proxy_url += '{}:{}'.format(str(proxy['proxy_host']), str(proxy['proxy_port']))

            vt = VideoTweet(
                video_path, consumer_key=auth.consumer_key, consumer_secret=auth.consumer_secret,
                access_token=auth.access_token, access_token_secret=auth.access_token_secret,
                proxy=proxy_url
            )
            vt.upload_init()
            vt.upload_append()
            vt.upload_finalize()
            result = vt.tweet(tweet)
            return result
        except:
            raise

    def get_additional_psychography(self, robot_id=None):
        conn = self.pool_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        additional_psychography = AdditionalRobotPsychography(conn, cursor)
        try:
            list_additional_psychography = additional_psychography.get_additional_psychography(robot_id)
            list_psychography = []
            sentiment = {"1": "positive", "0": "neutral", "-1": "negative"}
            if list_additional_psychography:
                for psychography in list_additional_psychography:
                    dict_psychography = {}
                    dict_psychography['psychography_id'] = psychography['psychography_id']
                    dict_psychography['psychography_name'] = psychography['p_desc']
                    dict_psychography['sentiment'] = sentiment[str(psychography['sentiment'])] if psychography[
                        'sentiment'] or psychography['sentiment'] == 0 else ""
                    if psychography['emotions']:
                        list_emotions = []
                        emotion_split = psychography['emotions'].split(",")
                        index = 0
                        while len(emotion_split) > index:
                            list_emotions.append(emotion_split[index])
                            index += 1
                        dict_psychography['emotions'] = list_emotions
                    else:
                        dict_psychography['emotions'] = []

                    list_psychography.append(dict_psychography)
                return list_psychography
            else:
                return []
        except Exception, e:
            logger.error(e)
            raise
        finally:
            cursor.close()
            conn.close()

    def auto_authorized(self, consumer_key, consumer_secret, robot, count_try=1, update_status=True):
        import time
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        robot_model = Robot(conn, cursor)
        try:
            if count_try > 2:
                time.sleep(5)

            auth = tweepy.OAuthHandler(consumer_key,
                                       consumer_secret, 'oob')
            redirect_url = auth.get_authorization_url()

            br = mechanize.Browser()
            br.set_handle_robots(False)  # ignore robots
            br.set_handle_refresh(False)  # can sometimes hang without this
            br.addheaders = [('User-agent', 'Firefox')]  # [('User-agent', 'Firefox')]

            br.open(redirect_url)

            br.form = list(br.forms())[0]

            control_username = br.form.find_control("session[username_or_email]")
            control_password = br.form.find_control("session[password]")

            if 'email' in robot and robot['email']:
                robot_username = robot['email']
            else:
                robot_username = robot['screen_name']

            control_username.value = robot_username
            control_password.value = robot['password']

            response = br.submit()

            current_url = br.geturl()

            if count_try < 5:
                if "challenge_type=RetypePhoneNumber" in current_url:
                    if 'phone_no' in robot and robot['phone_no']:
                        logger.info("Retype Number robot {}".format(robot['robot_id']), True)

                        br.form = list(br.forms())[0]
                        control_challange = br.form.find_control("challenge_response")
                        control_challange.value = robot['phone_no']
                        br.submit()
                        count_try += 1

                        return self.auto_authorized(consumer_key, consumer_secret, robot, count_try=count_try)
                    else:
                        logger.info("Retype Number but robot {} dont have phone no".format(robot['robot_id']), True)

                elif "challenge_type=RetypeEmail" in current_url:
                    if 'email' in robot and robot['email']:
                        logger.info("Retype Email robot {}".format(robot['robot_id']), True)
                        br.form = list(br.forms())[0]
                        control_challange = br.form.find_control("challenge_response")
                        control_challange.value = robot['email']
                        br.submit()
                        count_try += 1

                        return self.auto_authorized(consumer_key, consumer_secret, robot, count_try=count_try)
                    else:
                        logger.info("Retype Email but robot {} dont have email".format(robot['robot_id']), True)

            if current_url == 'https://api.twitter.com/oauth/authorize':

                result = response.read()

                verifier = self.find_between(result, "<code>", "</code>")

                try:
                    auth.get_access_token(verifier)

                    if robot["robot_status"] != 0 and update_status:
                        data = {robot_model.FIELD_STATUS: 1}
                        robot_model.update_by_data(data, robot['robot_id'])

                    return auth.access_token, auth.access_token_secret

                except tweepy.TweepError:
                    print 'Error! Failed to get access token.'
                    logger.error(tweepy.TweepError, sentry=self.sentry)
            else:
                if update_status:
                    data = {robot_model.FIELD_STATUS: 4}
                    robot_model.update_by_data(data, robot['robot_id'])
                    logger.info("Robot {} ({}) locked or wrong password".format(robot['robot_id'],
                                                                                robot['screen_name']), True)
            conn.commit()
        except Exception, e:
            conn.rollback()
            logger.error(e, sentry=self.sentry)
            raise
        finally:
            cursor.close()
            conn.close()

        return None, None

    def auto_authorized_selenium(self, consumer_key, consumer_secret, robot, update_status=True, port=None, proxy=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)

        robot_model = Robot(conn, cursor)
        rc_model = RobotCluster(conn_main, cursor_main)

        __dcap = DesiredCapabilities.PHANTOMJS
        __dcap['browserName'] = 'phantom'
        service_args = None
        if proxy:
            service_args = [
                '--proxy={}://{}:{}'.format(proxy['proxy_protocol'], proxy['proxy_host'], proxy['proxy_port']),
                '--proxy-type={}'.format(proxy['proxy_protocol']),
                '--ssl-protocol=any',
                '--ignore-ssl-errors=true'
            ]
            if 'proxy_username' in proxy and 'proxy_password' in proxy and proxy['proxy_username'] and proxy['proxy_password']:
                service_args.append('--proxy-auth={}:{}'.format(proxy['proxy_username'],
                                                                proxy['proxy_password']))

        if port:
            browser = webdriver.PhantomJS(executable_path=self.config.get("phantomjs", "path"),
                                          desired_capabilities=__dcap, port=int(port), service_args=service_args)
        else:
            browser = webdriver.PhantomJS(executable_path=self.config.get("phantomjs", "path"),
                                          desired_capabilities=__dcap, service_args=service_args)
        verifier = ''
        re_message = "Upload Failed"

        try:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret, 'oob')
            redirect_url = auth.get_authorization_url()
            browser.get(redirect_url)

            if 'screen_name' in robot and robot['screen_name']:
                robot_username = robot['screen_name']
            else:
                robot_username = robot['email']

            username = browser.find_element_by_name('session[username_or_email]')
            username.send_keys(robot_username)
            password = browser.find_element_by_name('session[password]')
            password.send_keys(robot['password'])
            password.send_keys(Keys.RETURN)

            if "challenge_type=RetypePhoneNumber" in browser.current_url:
                logger.info("RetypePhoneNumber {}".format(robot['screen_name']), True, config_load=self.config)
                phonenumber = browser.find_element_by_name('challenge_response')
                if 'phone_no' in robot and robot['phone_no']:
                    phonenumber.send_keys(robot['phone_no'], Keys.RETURN)
                    if "https://api.twitter.com/oauth/authorize?oauth_token=" in browser.current_url:
                        browser.find_element_by_id("allow").click()
                        if browser.current_url == 'https://api.twitter.com/oauth/authorize':
                            result = browser.page_source
                            verifier = self.find_between(result, "<code>", "</code>")
                    elif "incorrect_solution=true" in browser.current_url:
                        re_message = "Incorrect phone {}".format(robot['phone_no'])
                        logger.error(re_message, True, config_load=self.config)
                        verifier = "FAILED"
                else:
                    re_message = "No phone number {}".format(robot['screen_name'])
                    logger.error(re_message, True, config_load=self.config)
                    verifier = "FAILED"

            elif "challenge_type=RetypeEmail" in browser.current_url:
                logger.info("RetypeEmail {}".format(robot['screen_name']), True, config_load=self.config)
                user_email = browser.find_element_by_name('challenge_response')
                if 'email' in robot and robot['email']:
                    user_email.send_keys(robot['email'], Keys.RETURN)
                    if "https://api.twitter.com/oauth/authorize?oauth_token=" in browser.current_url:
                        browser.find_element_by_id("allow").click()
                        if browser.current_url == 'https://api.twitter.com/oauth/authorize':
                            result = browser.page_source
                            verifier = self.find_between(result, "<code>", "</code>")
                    elif "incorrect_solution=true" in browser.current_url:
                        re_message = "Incorrect email {}".format(robot['email'])
                        logger.error(re_message, True, config_load=self.config)
                        verifier = "FAILED"
                else:
                    re_message = "No email {}".format(robot['screen_name'])
                    logger.error(re_message, True, config_load=self.config)
                    verifier = "FAILED"

            elif "challenge_type=RetypeScreenName" in browser.current_url:
                logger.info("RetypeScreenName {}".format(robot['screen_name']), True, config_load=self.config)
                user_email = browser.find_element_by_name('challenge_response')
                if 'screen_name' in robot and robot['screen_name']:
                    user_email.send_keys(robot['screen_name'], Keys.RETURN)
                    if "https://api.twitter.com/oauth/authorize?oauth_token=" in browser.current_url:
                        browser.find_element_by_id("allow").click()
                        if browser.current_url == 'https://api.twitter.com/oauth/authorize':
                            result = browser.page_source
                            verifier = self.find_between(result, "<code>", "</code>")
                    elif "incorrect_solution=true" in browser.current_url:
                        re_message = "Incorrect screen name {}".format(robot['screen_name'])
                        logger.error(re_message, True, config_load=self.config)
                        verifier = "FAILED"
                else:
                    re_message = "No screen name {}".format(robot['email'])
                    logger.error(re_message, True, config_load=self.config)
                    verifier = "FAILED"

            elif browser.current_url == 'https://api.twitter.com/oauth/authorize':
                result = browser.page_source
                verifier = self.find_between(result, "<code>", "</code>")

            elif "challenge_type=TemporaryPassword" or "error" in browser.current_url:
                result = browser.page_source
                message = self.find_between(result, '<span class="message-text">', '</span>')
                if message:
                    err_message = message
                else:
                    err_message = "Need confirmation code"
                re_message = "TemporaryPassword or Error {} >>> {}".format(robot['screen_name'], err_message)
                logger.error(re_message, True, config_load=self.config)
                verifier = "FAILED"

            else:
                re_message = "UNKNOWN URL {} >>> {}".format(robot['screen_name'], browser.current_url)
                logger.error(re_message, True, config_load=self.config)
                verifier = "FAILED"

            if verifier and verifier != "FAILED":
                try:
                    auth.get_access_token(verifier)

                    if robot["robot_status"] != 0 and update_status:
                        rc_data = rc_model.get_by_robot_id(robot['robot_id'])
                        if rc_data:
                            data = {robot_model.FIELD_STATUS: 1}
                        else:
                            data = {robot_model.FIELD_STATUS: '0'}
                        robot_model.update_by_data(data, robot['robot_id'])

                    return auth.access_token, auth.access_token_secret, re_message

                except tweepy.TweepError:
                    print 'Error! Failed to get access token.'
                    logger.error(tweepy.TweepError, sentry=self.sentry, config_load=self.config)
            else:
                if update_status:
                    data = {robot_model.FIELD_STATUS: 4}
                    robot_model.update_by_data(data, robot['robot_id'])
                    logger.info("Robot {} ({}) locked or wrong password".format(
                        robot['robot_id'], robot['screen_name']), True, config_load=self.config)
                return None, None, re_message

            conn.commit()


        except Exception, e:
            conn.rollback()
            logger.error(e, sentry=self.sentry, config_load=self.config)
            raise
        finally:
            cursor.close()
            conn.close()
            try:
                browser.service.process.send_signal(signal.SIGTERM)
                browser.quit()
            except Exception, e:
                print "Browser already quit or something wrong"
                print e
                logger.error("Failed Quit Browser", sentry=self.sentry, config_load=self.config)
        return None, None, re_message

    def auto_authorization(self, consumer_key, consumer_secret, username, password):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, 'oob')

        redirect_url = auth.get_authorization_url()

        br = mechanize.Browser()
        br.set_handle_robots(False)  # ignore robots
        br.set_handle_refresh(False)  # can sometimes hang without this
        br.addheaders = [('User-agent', 'Firefox')]  # [('User-agent', 'Firefox')]

        br.open(redirect_url)

        br.form = list(br.forms())[0]

        control_username = br.form.find_control("session[username_or_email]")
        control_password = br.form.find_control("session[password]")

        control_username.value = username
        control_password.value = password

        response = br.submit()

        current_url = br.geturl()

        if current_url == 'https://api.twitter.com/oauth/authorize':

            result = response.read()

            verifier = self.find_between(result, "<code>", "</code>")

            try:
                auth.get_access_token(verifier)
            except tweepy.TweepError, e:
                raise
        else:
            raise Exception("This account locked or wrong password")

        return auth.access_token, auth.access_token_secret

    def get_range_time(self, tr):
        from datetime import datetime, timedelta
        today = datetime.today()
        date_list = list()
        for i in range(self.time_range[tr]):
            date_list.append((today - timedelta(days=i)))

        return date_list

    def get_start_end_date_by_tr(self, tr):
        dates = self.get_range_time(tr)
        return dates[-1].strftime("%Y%m%d"), dates[0].strftime("%Y%m%d")

    def get_data_from_carrot(self, carrot_host, query, limit=200):
        result = dict()
        try:
            query = quote(query)
            url = "{0}/xml?query={1}&results={2}&algorithm=lingo&SolrDocumentSource.solrIdFieldName=id&type=CARROT2".format(
                carrot_host, query, limit)
            response = requests.get(url)
            if response.status_code == 200:
                result = carrot_xml_parser_v2(response.content)
        except Exception:
            raise

        return result

    @staticmethod
    def get_start_end_date_by_year_month(year, month):
        from datetime import datetime
        dates = datetime.strptime(year, "%Y")
        s_date = dates.strftime("%Y%m%d")
        e_date = "{}1231".format(year)
        if month:
            dates = datetime.strptime("{}{}".format(year, month), "%Y%m")
            s_date = dates.strftime("%Y%m%d")
            e_date = (dates + relativedelta(day=31)).strftime("%Y%m%d")
        return s_date, e_date

    def get_token_facebook(self, account_id=None, status=None):
        conn = self.pool_isr_facebook.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        at_model = FBAccessToken(conn, cursor)
        date_now = datetime.datetime.now()
        try:
            token = at_model.find_token(account_id=account_id, status=status)
            if not token or not token['access_token']:
                raise Exception("Facebook Token not found Account {}".format(account_id))

            access_token = token['access_token']
            if token['access_token_valid'] <= date_now:
                ext_token, valid_time = get_extended_access_token(access_token, token['app_id'],
                                                                  token['app_secret'])
                if valid_time is None:
                    valid_time = date_now + datetime.timedelta(days=7)

                access_token = ext_token
                data = {
                    'access_token': access_token,
                    'access_token_valid': valid_time
                }
                at_model.update_data_at(data, token['access_token_id'])
                conn.commit()
                logger.info("Extended Token Valid Time {}".format(valid_time), True)

            return access_token
        except Exception:
            raise

    def set_general_activity_log(self, user_id=None, action=None, type=None, source_id=None, data_json=None):
        conn = self.pool_isr_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        gal_model = GeneralActivityLog(conn, cursor)
        try:
            gal_model.save_gal(user_id, action, type, source_id, data_json)
            conn.commit()
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def check_soldier_free_schedule(self, robot_id=None, hour=None, _type=None, decrease=True):
        conn = self.pool_main.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        ss_model = SoldierSchedule(conn, cursor)
        exist = False
        try:
            schedule = ss_model.get_robot_schedule(robot_id=robot_id, hour=hour, _type=_type).fetchone
            if schedule and schedule["count"] > 0:
                if decrease:
                    ss_model.decrease_counter(robot_id, hour, _type, schedule["count"])
                exist = True
            conn.commit()
        except Exception, e:
            logger.error(e)
            raise
        finally:
            cursor.close()
            conn.close()

        return exist

    def get_general_id(self, general_id=None, user_id=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        general_model = General(conn, cursor)
        try:
            data = general_model.select(general_id, user_id).fetchone
            return data
        except Exception:
            raise
        finally:
            conn.close()
            cursor.close()

    def tw_lookup_users(self, ids=None):
        try:
            apps_personal = self.get_twitter_apps_personal(random.choice(ids))
            if apps_personal:
                apps = apps_personal
            else:
                apps = self.get_apps_twitter(random.choice(ids))

            api = tweepy.API(auth_handler=self.get_auth(apps))
            result_tweet = to_dict(api.lookup_users(user_ids=ids))
            return result_tweet
        except tweepy.TweepError as e:
            try:
                code_error = e.message[0]['code']
                if code_error != 50:
                    logger.error(e)
            except:
                logger.error(e)
        except Exception:
            raise

    def get_robot_list_facebook(self, order_by="name ASC", robot_ids=None, keyword=None, start=None, rows=None,
                                rand=None, soldier_account=None):
        conn = self.pool_isr_facebook.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = FacebookSubs(conn, cursor)
            result = robot_model.get_robot(status=1, keyword=keyword, order_by=order_by, robot_ids=robot_ids,
                                             start=start, rows=rows, rand=rand, soldier_account=soldier_account)
            return {"data": result.fetchall, "count": result.rowscount}
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def get_robot_list_instagram(self, order_by="name ASC", keyword=None, robot_ids=None, start=None, rows=None):
        conn = self.pool_isr_instagram.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = InstagramSubs(conn, cursor)
            result = robot_model.get_robot(status=1, order_by=order_by, keyword=keyword, robot_ids=robot_ids,
                                             start=start, rows=rows)
            return {"data": result.fetchall, "count": result.rowscount}
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def get_robot_list_twitter(self, order_by="name ASC", robot_ids=None, start=None, rows=None, _type=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = Robot(conn, cursor)
            result = robot_model.get_robot(status=1, order_by=order_by, robot_ids=robot_ids,
                                             start=start, rows=rows, _type=_type)
            return {"data": result.fetchall, "count": result.rowscount}
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def get_robot_gmail_account(self, robot_ids=None, order="RAND()", start=None, rows=None):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            robot_model = Robot(conn, cursor)
            result = robot_model.get_robot_gmail(robot_ids=robot_ids, status=1, start=start, rows=rows, order=order)
            return {"data": result.fetchall, "count": result.rowscount}
        except Exception:
            raise
        finally:
            cursor.close()
            conn.close()

    def set_robot_activity_log(self, robot_id=None, socmed=None, _type=None, source_id=None):
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        rl_model = RobotLog(conn_main, cursor_main)
        try:
            rl_model.save_rl(robot_id, socmed, _type, source_id)
            conn_main.commit()
        except Exception:
            raise
        finally:
            cursor_main.close()
            conn_main.close()

    def get_utils_object(self):
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        psycho_catalog_model = PsychographyCatalog(conn_main, cursor_main)
        try:
            psychography_catalog = psycho_catalog_model.get_psychographycal_catalog().fetchall
            utilobj = Utils(dbname="mongo_db", configObj=self.config, get_ugc=False,
                            psychography_catalog=psychography_catalog, disable_logger=True)
            return utilobj
        except Exception:
            raise
        finally:
            cursor_main.close()
            conn_main.close()

    def regenerate_apps(self, twitter_account_id, apps):
        conn = self.pool_isr_twitter.connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        robot_model = Robot(conn, cursor)
        apps_model = ApplicationsPersonal(conn, cursor)
        wc_model = WordsCatalog(conn_main, cursor_main)
        sc_model = SentencesCatalog(conn_main, cursor_main)
        from eblib.twitter_report import Twitter_report
        bw = Twitter_report(driver_name='phantomjs',
                            executable_path='phantomjs')
        try:
            print "Regenerate Apps"
            # Make Name
            apps_name = None
            initials_apps_clinet = self.config.get("apps_catalog", "initials_apps_client")
            run_name = True
            while (run_name):
                words_catalog = wc_model.find_rand(start=0, rows=2).fetchall
                words = []
                if words_catalog:
                    for wc in words_catalog:
                        words.append(wc["wc_word"])
                apps_name = " ".join(words)
                random_length = random.randint(0, len(list(apps_name)))
                apps_name = apps_name[:int(random_length)] + '{}'.format(initials_apps_clinet) + \
                            apps_name[int(random_length):]
                apps_name = apps_name.lower()
                apps_name = apps_name.title()
                check_name = self.ssdb.hget(name=self.config.get("ssdb", "apps_catalog_topic"),
                                            key=apps_name)
                if not check_name:
                    apps_name = apps_name
                    run_name = False
            # Make URL
            random_domain = random.choice([".com", ".org", ".net", ".biz", ".info", ".asia",
                                           ".co.id", ".go.id", ".net.id", "web.id"])
            random_protocol = random.choice(["http://", "https://"])
            apps_url = "{}{}{}".format(random_protocol, apps_name.replace(" ", "").lower(), random_domain)
            # Make Description
            apps_desc = None
            sentences = []
            run_sentences = True
            # Looping if content < 10
            while (run_sentences):
                sentences_catalog = sc_model.find_rand(start=0, rows=1, pub_date="{}".format(
                    datetime.datetime.now().strftime("%Y-%m-%d"))).fetchone
                if sentences_catalog:
                    content = str(sentences_catalog["sc_content"]).replace("-", "").replace("!", "") \
                        .replace("@", "").replace("#", "").replace("$", "").replace("%", "") \
                        .replace("^", "").replace("&", "").replace("(", "").replace(")", "") \
                        .replace("=", "").replace("+", "").replace("[", "").replace("]", "") \
                        .replace("{", "").replace("}", "").replace(";", "").replace(":", "") \
                        .replace("'", "").replace(",", "").replace("\n", "").replace("\r", "") \
                        .replace("\"", "")
                    if list(content) > 10:
                        sentences.append(content)
                        run_sentences = False
                else:
                    sentences_catalog = sc_model.find_rand(start=0, rows=1).fetchone
                    if sentences_catalog:
                        content = str(sentences_catalog["sc_content"]).replace("-", "").replace("!", "") \
                            .replace("@", "").replace("#", "").replace("$", "").replace("%", "") \
                            .replace("^", "").replace("&", "").replace("(", "").replace(")", "") \
                            .replace("=", "").replace("+", "").replace("[", "").replace("]", "") \
                            .replace("{", "").replace("}", "").replace(";", "").replace(":", "") \
                            .replace("'", "").replace(",", "").replace("\n", "").replace("\r", "") \
                            .replace("\"", "")
                        if list(content) > 10:
                            sentences.append(content)
                            run_sentences = False
                    else:
                        raise Exception("Sentences Catalog Not Found")
            # Looping if text < 10 OR > 200
            run_generator = True
            while (run_generator):
                markov = markovgen.Markov(sentences)
                text = markov.generate_markov_text()
                if len(text) > 10 and len(text) < 200:
                    apps_desc = "{}".format(text.title())
                    run_generator = False

            robot = robot_model.get_robot(twitter_account_id=twitter_account_id).fetchone
            proxy = self.get_robot_proxy(robot['robot_id'])
            bw.prepare(None, username=robot['email'], password=robot['password'],
                       phone_no=robot['phone_no'], screen_name=robot['screen_name'], proxy=proxy)
            res = bw.activity.create_apps(apps_name=apps_name, apps_desc=apps_desc, apps_url=apps_url)
            if 'status' in res:
                return "failed", res['status']
            else:
                if apps:
                    apps_model.delete(app_id=apps['app_id'])
                apps_model.insert(app_id=res['app_id'], app_name=res['app_name'],
                                  consumer_key=res['consumer_key'],
                                  consumer_secret=res['consumer_secret'],
                                  twitter_account_id=robot['twitter_account_id'],
                                  access_token=res['access_token'],
                                  access_token_secret=res['access_token_secret'],
                                  app_status='0')
                conn.commit()
                return "success", res
        except:
            raise
        finally:
            cursor.close()
            conn.close()
            bw.atexit()

    def get_cluster_by_user(self, u_id):
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        try:
            user_model = User(conn_main, cursor_main)
            user = user_model.get_user(u_id=u_id)
            return user.fetchone['c_id']
        except:
            raise
        finally:
            cursor_main.close()
            conn_main.close()

    def set_robot_log(self, robot_id, _type, action, cac_id):
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        try:
            rl_model = RobotLog(conn_main, cursor_main)
            rl_model.save_rl(robot_id, _type, action, cac_id)
            conn_main.commit()
        except:
            raise
        finally:
            cursor_main.close()
            conn_main.close()

    def get_robot_proxy(self, robot_id, socmed='twitter'):
        conn_main = self.pool_isr_main.connection()
        cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
        try:
            if robot_id:
                if socmed == 'twitter':
                    rp_model = RobotProxyNew(conn_main, cursor_main)
                    result = rp_model.get_robot_proxy(robot_id=robot_id).fetchone
                else:
                    rp_model = RobotFbProxy(conn_main, cursor_main)
                    result = rp_model.get_proxy_by_robot_id(robot_id).fetchone
                conn_main.commit()

                if result:
                    proxy_url = "{}://".format(str(result['proxy_protocol']))
                    if result['proxy_username'] and result['proxy_password']:
                        proxy_url += '{}:{}@'.format(str(result['proxy_username']), str(result['proxy_password']))
                    proxy_url += '{}:{}'.format(str(result['proxy_host']), str(result['proxy_port']))

                    self.proxy_check(proxy_url, robot_id=robot_id, socmed=socmed, proxy_id=result['proxy_id'])

                return result
            else:
                return None
        except:
            raise
        finally:
            cursor_main.close()
            conn_main.close()

    def proxy_check(self, proxy, attempt=0, robot_id=None, socmed='twitter', proxy_id=None):
        max_attempt = 3
        try:
            url = 'http://twitter.com/' if socmed == 'twitter' else 'http://facebook.com/'
            requests.get(url, proxies={
                "http": proxy,
                "https": proxy
            })

            return True
        except Exception:
            if attempt < max_attempt:
                logger.error("Could not connect to proxy {}. Attempt {}".format(proxy, attempt))
                attempt += 1
                self.proxy_check(proxy, attempt, robot_id, socmed, proxy_id)
            else:
                if socmed == 'twitter':
                    conn = self.pool_isr_twitter.connection()
                    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
                    conn_main = self.pool_isr_main.connection()
                    cursor_main = conn_main.cursor(MySQLdb.cursors.DictCursor)
                    try:
                        r = Robot(conn, cursor)
                        p = Proxy(conn_main, cursor_main)
                        r.update_status_by_robot_ids(status='11', robot_ids=robot_id)
                        p.update_proxy({
                            p.FIELD_STATUS: '0'
                        }, proxy_id)

                        conn.commit()
                        conn_main.commit()
                    except:
                        conn.rollback()
                        conn_main.rollback()
                    finally:
                        cursor.close()
                        conn.close()
                        cursor_main.close()
                        conn_main.close()

                raise Exception('Proxy Error')
