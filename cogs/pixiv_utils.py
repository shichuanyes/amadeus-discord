import os.path
import pickle
import time
from collections import deque
from typing import Dict, List

from pixivpy3 import AppPixivAPI
from pixivpy3.utils import ParsedJson


class Pixiv:
    def __init__(
            self,
            refresh_token: str,
            history_size: int = 100,
            file_size_limit: int = 8e6,
            history_pickle_file: str = "history.pkl"
    ):
        self.refresh_token: str = refresh_token
        self.file_size_limit = file_size_limit

        self.api = AppPixivAPI()
        if history_pickle_file and os.path.exists(history_pickle_file):
            with open(history_pickle_file, "rb") as f:
                self.history = pickle.load(f)
        else:
            self.history = deque(maxlen=history_size)

        self.access_token_expiration: int = 0

    def auth_if_expired(self) -> bool:
        now = time.time()
        if now > self.access_token_expiration:
            response = self.api.auth(refresh_token=self.refresh_token)
            self.access_token_expiration = now + response.expires_in
            return True
        return False

    def search_illust(
            self,
            word: str,
            search_target: str = "partial_match_for_tags",
            sort: str = "popular_desc",
            duration: str = None,
            start_date: str | None = None,
            end_date: str | None = None,
    ) -> ParsedJson | None:
        self.auth_if_expired()

        response = self.api.search_illust(
            word=word,
            search_target=search_target,
            sort=sort,
            duration=duration,
            start_date=start_date,
            end_date=end_date
        )

        if not response.illusts or len(response.illusts) == 0:
            return None

        result = self._select_illust(response.illusts)
        self.history.append(result.id)
        return result

    def _select_illust(self, illusts: List[ParsedJson]) -> ParsedJson:
        result = None
        min_ = len(self.history)
        for illust in illusts:
            try:
                idx = self.history.index(illust.id)
            except ValueError:
                return illust
            if min_ > idx:
                min_ = idx
                result = illust
        del self.history[min_]
        return result

    def illust_detail(
            self,
            illust_id: int | str
    ) -> ParsedJson | None:
        self.auth_if_expired()

        response = self.api.illust_detail(illust_id=illust_id)
        if not response:
            return None
        return response.illust

    @staticmethod
    def parse_image_urls(
            illust: ParsedJson,
            page: int = 0
    ) -> Dict:
        if illust.meta_single_page:
            result = illust.image_urls
            result['original'] = illust.meta_single_page.original_image_url
            return result
        else:
            return illust.meta_pages[page].image_urls

    def download(
            self,
            urls: ParsedJson,
            directory: str,
    ) -> str:
        file = self._download(urls.original, directory)
        if os.path.getsize(file) > self.file_size_limit:
            file = self._download(urls.large, directory)
        return file

    def _download(
            self,
            url: str,
            directory: str
    ) -> str:
        self.auth_if_expired()

        self.api.download(url, path=directory)
        return os.path.join(directory, os.path.basename(url))

    def save_history(self, file: str = "history.pkl") -> None:
        with open(file, 'wb') as f:
            pickle.dump(self.history, f)
