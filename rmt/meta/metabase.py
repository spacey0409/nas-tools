from functools import lru_cache
import requests
from requests import RequestException

import log
from config import FANART_TV_API_URL, FANART_MOVIE_API_URL, ANIME_GENREIDS, Config
from rmt.category import Category
from utils.types import MediaType


class MetaBase(object):
    """
    媒体信息基类
    """
    proxies = None
    category_handler = None
    # 原字符串
    org_string = None
    # 副标题
    subtitle = None
    # 类型 电影、电视剧
    type = None
    # 识别的中文名
    cn_name = None
    # 识别的英文名
    en_name = None
    # 总季数
    total_seasons = 0
    # 识别的开始季 数字
    begin_season = None
    # 识别的结束季 数字
    end_season = None
    # 总集数
    total_episodes = 0
    # 识别的开始集
    begin_episode = None
    # 识别的结束集
    end_episode = None
    # Partx Cd Dvd Disk Disc
    part = None
    # 识别的资源类型
    resource_type = None
    # 识别的分辨率
    resource_pix = None
    # 二级分类
    category = None
    # TMDB ID
    tmdb_id = 0
    # 媒体标题
    title = None
    # 媒体原发行标题
    original_title = None
    # 媒体年份
    year = None
    # 封面图片
    backdrop_path = None
    poster_path = None
    fanart_image = None
    # 评分
    vote_average = 0
    # 描述
    overview = None
    # TMDB 的其它信息
    tmdb_info = {}
    # 种子附加信息
    site = None
    site_order = 0
    enclosure = None
    res_order = 0
    size = 0
    seeders = 0
    peers = 0
    description = None

    def __init__(self, title, subtitle=None):
        if not title:
            return
        config = Config()
        self.proxies = config.get_proxies()
        self.category_handler = Category()
        self.org_string = title
        self.subtitle = subtitle

    def get_name(self):
        if self.cn_name:
            return self.cn_name
        if self.en_name:
            return self.en_name
        return ""

    def get_title_string(self):
        return "%s (%s)" % (self.title, self.year) if self.year else self.title

    def get_vote_string(self):
        if self.vote_average:
            return "评分：%s" % self.vote_average
        else:
            return ""

    def get_title_vote_string(self):
        if not self.vote_average:
            return self.get_title_string()
        else:
            return "%s %s" % (self.get_title_string(), self.get_vote_string())

    # 返回季字符串
    def get_season_string(self):
        if self.begin_season is not None:
            return "S%s" % str(self.begin_season).rjust(2, "0") \
                if self.end_season is None \
                else "S%s-S%s" % \
                     (str(self.begin_season).rjust(2, "0"),
                      str(self.end_season).rjust(2, "0"))
        else:
            if self.type == MediaType.MOVIE:
                return ""
            else:
                return "S01"

    # 返回begin_season 的Sxx
    def get_season_item(self):
        if self.begin_season is not None:
            return "S%s" % str(self.begin_season).rjust(2, "0")
        else:
            if self.type == MediaType.MOVIE:
                return ""
            else:
                return "S01"

    # 返回季的数组
    def get_season_list(self):
        if self.begin_season is None:
            if self.type == MediaType.MOVIE:
                return []
            else:
                return [1]
        elif self.end_season is not None:
            return [season for season in range(self.begin_season, self.end_season + 1)]
        else:
            return [self.begin_season]

    # 返回集字符串
    def get_episode_string(self):
        if self.begin_episode is not None:
            return "E%s" % str(self.begin_episode).rjust(2, "0") \
                if self.end_episode is None \
                else "E%s-E%s" % \
                     (
                         str(self.begin_episode).rjust(2, "0"),
                         str(self.end_episode).rjust(2, "0"))
        else:
            return ""

    # 返回集的数组
    def get_episode_list(self):
        if self.begin_episode is None:
            return []
        elif self.end_episode is not None:
            return [episode for episode in range(self.begin_episode, self.end_episode + 1)]
        else:
            return [self.begin_episode]

    # 返回集的并列表达方式，用于支持单文件多集
    def get_episode_items(self):
        return "E%s" % "E".join(str(episode).rjust(2, '0') for episode in self.get_episode_list())

    # 返回季集字符串
    def get_season_episode_string(self):
        if self.type == MediaType.MOVIE:
            return ""
        else:
            seaion = self.get_season_string()
            episode = self.get_episode_string()
            if seaion and episode:
                return "%s %s" % (seaion, episode)
            elif seaion:
                return "%s" % seaion
            elif episode:
                return "%s" % episode
        return ""

    # 返回资源类型字符串
    def get_resource_type_string(self):
        if self.resource_type and self.resource_pix:
            return "%s %s" % (self.resource_type, self.resource_pix)
        elif self.resource_type:
            return self.resource_type
        elif self.resource_pix:
            return self.resource_pix
        else:
            return ""

    # 返回背景图片地址
    def get_backdrop_path(self):
        if self.fanart_image:
            return self.fanart_image
        elif self.backdrop_path:
            return self.backdrop_path
        else:
            return "../static/img/tmdb.webp"

    # 返回消息图片地址
    def get_message_image(self):
        if self.fanart_image:
            return self.fanart_image
        elif self.poster_path:
            return self.poster_path
        else:
            return "../static/img/tmdb.webp"

    # 是否包含季
    def is_in_season(self, season):
        if isinstance(season, list):
            if self.end_season is not None:
                meta_season = list(range(self.begin_season, self.end_season + 1))
            else:
                if self.begin_season is not None:
                    meta_season = [self.begin_season]
                else:
                    meta_season = [1]

            return set(meta_season).issuperset(set(season))
        else:
            if self.end_season is not None:
                return self.begin_season <= int(season) <= self.end_season
            else:
                if self.begin_season is not None:
                    return int(season) == self.begin_season
                else:
                    return int(season) == 1

    # 是否包含集
    def is_in_episode(self, episode):
        if isinstance(episode, list):
            if self.end_episode is not None:
                meta_episode = list(range(self.begin_episode, self.end_episode + 1))
            else:
                meta_episode = [self.begin_episode]
            return set(meta_episode).issuperset(set(episode))
        else:
            if self.end_episode is not None:
                return self.begin_episode <= int(episode) <= self.end_episode
            else:
                return int(episode) == self.begin_episode

    # 整合TMDB识别的信息
    def set_tmdb_info(self, info):
        if not info:
            return
        self.type = self.__get_tmdb_type(info)
        if not self.type:
            return
        self.tmdb_id = info.get('id')
        if not self.tmdb_id:
            return
        self.tmdb_info = info
        self.vote_average = info.get('vote_average')
        self.overview = info.get('overview')
        if self.type == MediaType.MOVIE:
            self.title = info.get('title')
            self.original_title = info.get('original_title')
            release_date = info.get('release_date')
            if release_date:
                self.year = release_date[0:4]
            self.category = self.category_handler.get_movie_category(info)
        else:
            self.title = info.get('name')
            self.original_title = info.get('original_name')
            first_air_date = info.get('first_air_date')
            if first_air_date:
                self.year = first_air_date[0:4]
            if self.type == MediaType.TV:
                self.category = self.category_handler.get_tv_category(info)
            else:
                self.category = self.category_handler.get_anime_category(info)
        self.poster_path = "https://image.tmdb.org/t/p/w500%s" % info.get('poster_path') if info.get('poster_path') else ""
        self.fanart_image = self.get_fanart_image(search_type=self.type, tmdbid=info.get('id'))
        self.backdrop_path = "https://image.tmdb.org/t/p/w500%s" % info.get('backdrop_path') if info.get('backdrop_path') else ""

    # 整合种了信息
    def set_torrent_info(self,
                         site=None,
                         site_order=0,
                         enclosure=None,
                         res_order=0,
                         size=0,
                         seeders=0,
                         peers=0,
                         description=None):
        self.site = site
        self.site_order = site_order
        self.enclosure = enclosure
        self.res_order = res_order
        self.size = size
        self.seeders = seeders
        self.peers = peers
        self.description = description

    # 获取消息媒体图片
    # 增加cache，优化资源检索时性能
    @classmethod
    @lru_cache(maxsize=256)
    def get_fanart_image(cls, search_type, tmdbid, default=None):
        if not search_type:
            return ""
        if tmdbid:
            if search_type == MediaType.MOVIE:
                image_url = FANART_MOVIE_API_URL % tmdbid
            else:
                image_url = FANART_TV_API_URL % tmdbid
            try:
                ret = requests.get(image_url, timeout=10, proxies=cls.proxies)
                if ret:
                    moviethumbs = ret.json().get('moviethumb')
                    if moviethumbs:
                        moviethumb = moviethumbs[0].get('url')
                        if moviethumb:
                            # 有则返回FanArt的图片
                            return moviethumb
            except RequestException as e1:
                log.console(str(e1))
            except Exception as e2:
                log.console(str(e2))
        if default:
            # 返回一个默认图片
            return default
        return ""

    # 判断电视剧是否为动漫
    def __get_tmdb_type(self, info):
        if not info:
            return self.type
        if not info.get('media_type'):
            return self.type
        if info.get('media_type') == MediaType.TV:
            genre_ids = info.get("genre_ids")
            if not genre_ids:
                return MediaType.TV
            if isinstance(genre_ids, list):
                genre_ids = [str(val).upper() for val in genre_ids]
            else:
                genre_ids = [str(genre_ids).upper()]
            if set(genre_ids).intersection(set(ANIME_GENREIDS)):
                return MediaType.ANIME
            else:
                return MediaType.TV
        else:
            return info.get('media_type')
