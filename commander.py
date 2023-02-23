import collections
import dataclasses
import enum
import typing as ty
from abc import abstractmethod
from datetime import datetime
from typing import Protocol, runtime_checkable

import frozendict as frozendict
from Yandex import DiskAPI as ya
from ordered_set import OrderedSet


# from ABC


@dataclasses.dataclass
class HashOfFile:
    md5: str
    sha256: str
    size: int

    def __hash__(self):
        return hash((self.md5, self.sha256, self.size))


@dataclasses.dataclass
class Resource:
    is_folder: bool
    path: bool
    name: str
    full_name: str
    created: datetime
    modified: datetime

    def __hash__(self):
        return hash(self.full_name)


#    full_path: str


@dataclasses.dataclass
class FileInfo(Resource):
    size: int
    md5: str
    sha256: str

    # hash: HashOfFile

    def __hash__(self):
        return hash((self.md5, self.sha256, self.size))

    #
    # def __hash__(self):
    #     return hash(self.hash)


@dataclasses.dataclass
class FolderInfo(Resource):
    ...

    # items: ty.Iterable[ty.Self]


# def walk(path: str) -> ty.Iterable[Resource, ty.Iterable[Resource], ty.Iterable[Resource]]:
#     """
#
#     Parameters
#     ----------
#     path :
#
#     Returns
#     -------
#
#     """
#
#     buffer_files = collections.deque()
#     buffer_folders = collections.deque()
#     # manager = self.get_manager(path)
#     root = manager.get(path)
#
#     def folders() -> ty.Iterable[Resource]:
#         nonlocal root
#         while len(buffer_folders) > 0:
#             yield buffer_folders.pop()
#
#         for item in root.items:
#             if item.is_folder:
#                 yield item
#             else:
#                 buffer_files.appendleft(item)
#
#     def files() -> ty.Iterable[Resource]:
#         nonlocal root
#         while len(buffer_files) > 0:
#             yield buffer_files.pop()
#
#         for item in root.items:
#             if not item.is_folder:
#                 yield item
#             else:
#                 buffer_folders.appendleft(item)
#
#     return root, folders(), files()
#


class TypeMedia(enum.Enum):
    local = enum.auto()
    cloud = enum.auto()


class BaseFS(Protocol):
    @abstractmethod
    def touch(self, path_to_file: str):
        ...

    @abstractmethod
    def mkdir(self, path_to_folder: str):
        ...

    @abstractmethod
    def rm(self, path: str):
        ...

    @abstractmethod
    def cp(self, path: str, target: str, overwrite: bool = False):
        ...

    def ls(self, path_to_folder: str = None) -> ty.Iterable[FileInfo]:
        ...

    def get_hash(self, file: str) -> HashOfFile:
        ...

    def exist(self, path: str) -> bool:
        ...

    def get(self, path: str) -> FileInfo | None:
        ...


# @dataclasses.dataclass
# class ResourceOfFS:
#     resource: Resource
#     fs: BaseFS


@runtime_checkable
class RemoteFS(Protocol):
    @abstractmethod
    def download(self, path: str, target: str):
        ...

    @abstractmethod
    def upload(self, path: str, target: str):
        ...


@runtime_checkable
class LocalExtFS(Protocol):
    ...


# class CloudFS(BaseFS, CloudExtFS):
#    ...


# class LocalFS(BaseFS, LocalExtFS):
#    ...


class TempFS(BaseFS):
    def create(self, path: str = None):
        raise NotImplemented


class LocalFS(BaseFS, LocalExtFS):
    ...


#
# class YandexFS(BaseFS, RemoteFS):
#     resource_cache: dict[str, Resource]
#     disk: ya.Disk = None
#
#     def is_cached(self, path: str) -> bool:
#         return path in self.resource_cache
#
#     def _get_from_cache(self, path: str) -> Resource:
#         return self.resource_cache.get(path, None)
#
#     def _put_to_cache(self, resource: Resource):
#         # for item in list(resource):
#         self.resource_cache[resource.full_path] = resource
#
#     # def get_subitems(self, owner: str) -> ty.Iterable[Resource]:
#     #    ...
#     @classmethod
#     def _create_resource(cls, ya_resource: ya.Resource) -> Resource:
#         def items(res: Resource) -> ty.Iterable[Resource]:
#             ...
#
#         resource = Resource()
#         resource.items = items(resource)
#         return resource
#
#     def get(self, path: str) -> Resource:
#         if not self.is_cached(path):
#             status, response = self.disk.resource_info(path)
#             resource = self._create_resource(response)
#             self._put_to_cache(resource)
#         return self.resource_cache[path]
#
#     def mkdir(self, path: str):
#         self.disk.mkdir(path)
#
#     def rm(self, path: str):
#         self.disk.remove_resource(path)
#
#     def mv(self, path: str, target: str, overwrite: bool = False):
#         self.disk.move_resource(path, target, overwrite=overwrite)
#
#     def cp(self, path: str, target: str, overwrite: bool = False):
#         self.disk.copy_resource(path, target, overwrite=overwrite)
#
#     def _url_download(self, url: str, target: str):
#         ...
#
#     def download(self, path: str, target: str, overwrite: bool = False):
#         status, link = self.disk.download_resource(path)
#         self._url_download(link.href, target)
#

# class ResourceManagerYandex(ResourceManager):
#     disk: api.Disk = None
#     _request_cache: dict[str, dict]
#
#     def get_subitems(self, owner: Resource) -> ty.Iterable[Resource]:
#         ...
#
#     def get(self, path: str) -> Resource:
#         if not self.is_cached(path):
#             status, resource = self.disk.resource_info()
#             self._put_to_cache(resource)
#         return self._get_from_cache(path)
#
#     def _get_resource(self, owner: str) -> ty.Iterable[Resource]:
#         response: dict[str, api.Resource]
#         if owner in self._request_cache:
#             response = self._request_cache[owner]
#         else:
#             status, response = self.disk.resource_info(owner)
#         return
#
#         # item: api.ResourceShort = next(root._embedded.items)


# class HashInfo:
#     paths: dict[str, FileInfo]
#     """
#     key - path to file with name
#     """

# MountPoint: ty.TypeAlias = str


# @dataclasses.dataclass
class FSLayer(BaseFS):
    key: str
    fs: BaseFS
    params: dict

    def __hash__(self):
        return hash(self.key)

    # @classmethod
    def find_file(self, full_filename: str) -> FileInfo | None:
        return next(
            (
                file_on_layer
                for file_on_layer in self.ls()
                if file_on_layer.full_name == full_filename
            ),
            None,
        )  # Поиск файла на слое


# K = ty.TypeVar("K")
# V = ty.TypeVar("V")

# class ResourceIterator
# class FSPool(ty.Generic[K,V],dict):
#     #_fs_items: dict[str, FSItem]
#
#     def attach(self, fs: FSItem):
#         self._fs_items[fs.key] = fs
#
#     def __getitem__(self, key):
#         return self._fs_items[key]
#
#     def __setitem__(self, key, value):
#         self._fs_items[key] = value
#
#     def __


@dataclasses.dataclass
class FileOnLayer:
    resource: FileInfo | None
    fs: FSLayer


class FSLayersPool(dict[str, FSLayer]):
    def attach(self, fs: FSLayer):
        self[fs.key] = fs

    def find_file(self, full_pathname: str) -> list[FileOnLayer]:
        ...


class CopyError(Exception):
    ...


class UnionFS:
    # layers: dict[str, BaseFS] = {}
    layers: FSLayersPool
    # слои FS, ключ - имя слоя уникальное имя
    mode: ty.Literal["mirror", "union"] = "mirror"

    # mirror - Зеркальные копии
    # union - слои присоединенных FS образуют общую FS

    # file_on_layers: ty.TypeAlias = tuple[Resource | None]
    # Файл с одним full_name/hash на всех слоях FS, None - файла в слое нет
    # длина кортежа равна длине словаря layers, позиция в кортеже соответствует позиции в layers

    def sync(self):
        """
        В режиме mirror - каждый слой копия других
        Returns
        -------

        """

        # def find_on_layers(file_fullname: str) -> list[ResourceOnFSLayer]:
        #     """
        #     Ищет файл c таким fullname во всех слоях
        #     Parameters
        #     ----------
        #     file_fullname :
        #
        #     Returns
        #     -------
        #     кортеж ключей - ключей layers, где найдено
        #     """
        #     ...

        # s: ty.ItemsView[str, BaseFS] = None
        # a, b = s

        def ls_files(fs: FSLayer) -> list[FileInfo]:
            ...

        def fastest_sources_for_copyfrom(_from: FSLayer) -> tuple[str]:
            ...

        def inexpensive_sources_for_copyfrom(_from: FSLayer) -> tuple[str]:
            ...

        def reasonsable_sources_for_copyto(
            _from: list[FSLayer],
            target: FSLayer,
            strategy: str = "fastest",
        ) -> list[FSLayer]:
            ...

        def select_newest_files_from(
            files: list[FileOnLayer],
        ) -> list[FileOnLayer] | None:
            ...

        def copy_from(sources: list[FileOnLayer], targets: list[FileOnLayer]):
            """
            Копирование файла из sources (выбрать лучший вариант), в слои targets
            :param sources: Возможные источники с файлом
            :type sources: список файла на разных слоях
            :param targets:
            :type targets:
            :return:
            :rtype:
            """

            def try_copy(source: FileOnLayer, target: FileOnLayer) -> bool:
                raise NotImplemented

            for target in targets:
                for layer in reasonsable_sources_for_copyto(
                    [flayer.fs for flayer in sources], target.fs
                ):
                    """
                    Слои откуда копируем
                    """
                    copy_success = False
                    for copy_source in [flayer for flayer in sources if flayer.fs is layer]:
                        if not try_copy(copy_source, target):
                            # Копирование не удалось, пробуем из другого слоя
                            continue
                        copy_success = True
                        break
                    if not copy_success:
                        raise CopyError

        # def cost_copy(to_fs: BaseFS) -> tuple[int]:
        #     """
        #     Список стоимости копирования данных из FS в layers
        #     Parameters
        #     ----------
        #     to_fs :
        #
        #     Returns
        #     -------
        #     кортеж стоимости по возрастанию с индексами FS в layers
        #     """
        #     ...

        def layer_available(fs: FSLayer) -> bool:
            ...

        # processed_file = []
        # for fs_name, fs in self.layers.items():
        #     for resource in ls_files(fs):
        #         find_result = find_on_layers(resource.full_name)
        #         if len(find_result) == len(self.layers):
        #             # Найден на всех слоях
        #             processed_file += resource
        #             continue
        #         newest_files = find_newest_resources(find_result)
        #         for layer_name, layer in self.layers.items():
        #             file_on_layer = next((obj for obj in find_result if obj.fs == layer), None)
        #             if file_on_layer is None or file_on_layer not in newest_files:
        #                 # Если файл отсутствует, или он устаревший
        #                 sources = reasonsable_sources_for_copyfrom(layer)
        #                 for sources in sources:
        #                     if not fs_available(sources):
        #                         continue
        #                     sources.cp(
        #                         resource.full_name,
        #                     )

        """
        Синхронизация S слоев пула. Режим "зеркало". Алгоритм
        Составляем цепочки файлов с одинаковыми полными именами в слоях.
        Номер позиции в цепочке равен N (номер слоя) 
        1. Для файла F из слоя N с полным именем K (путь к файлу+имя файла), не входящего в список "не синхронизируемые", 
        помещаем в цепочку, в слое N+1 ищем файл F1 с полным именем K.
        Если не найден, помещаем в цепочку None (помечаем F1 как отсутствующий). Помечаем цепочку как неуспешную. 
        Повторяем для файла F и всех слоев пула. 
        Если F1 найден, помещаем в цепочку, сравниваем хэш F и F1. 
        Если хэш совпал считаем что слои  N и N1 по файлу F равны, если хэш не совпал помечаем помечаем цепочку как неуспешную.  
        Повторяем для файла F и всех слоев пула. 
        Если для всех слоев S сравнение успешно, помечаем цепочку F..F[S] как успешную. 
        2. Повторяем 1 для всех файлов в слое ранее не вошедших в цепочки.
        
        Начинаем с самых длинных цепочек:
        3. Выбираем следующую неуспешную цепочку N
        для имеющихся файлов в цепочке, запустить процедуру "выбрать самые актуальные из списка". Если процедура
        успешна, запустить процедуру для актуального "копирование файлов(список возможных источников) в слой" для слоев с 
        отличающимися или отсутствующими файлами, пометить цепочку как успешную. Если "выбрать самый актуальный из списка" 
        неуспешна, пометить цепочку как не синхронизируемые и требующую ручного разрешения конфликта. Повторить 3. 
        4. "копирование файла F в слой N"
            Предполагается, что копирование внутри слоя самое "дешевое и быстрое". 
            Для F вычислить хэш H. В слое N попытаться найти файл с хэшем H. Если найден файл S, 
            если S один в своей цепочке K, переименовать S в полный путь F, цепочку K удалить. Если S не один в цепочке,
            если допустимо слоем и СТРАТЕГИЕЙ создавать линки внутри слоя, создать линк на S с полный путь F, иначе копирование
            S в файл с полный путь F.
            Если в слое N не найден файл с хэшем H.
            Для копирования в слой N из списка источников выбрать самый подходящий K в соответствии со СТРАТЕГИЕЙ.
            Копирование F из K в слой N в файл с полный путь F.
              
        5. "выбрать самый актуальный из списка"
            Безошибочного способа выбрать самый актуальный файл из разных, управляемых не с единой точки хранилищ, нет.
            Можно основываться на дате последней модификации файла, если часы хранилищ гарантированно синхронизированы.
            Часы облачных хранилищ, как правило синхронизированы с мировым временем, часы локального компьютера с подключением
            в Интернет, как правило, тоже. С переносными хранилищами уверенности нет.
            Можно использовать режим "доверять часам", и основываться на времени модификации.
        """

        def in_blacklist(file: FileInfo) -> bool:
            ...

        layer_num = 0
        layers_items = self.layers.items()
        unsuccessful_chains: set[list[FileInfo | None]] = set()
        manual_control_needed = []
        for layer_name1, layer1 in layers_items:
            layer1_ls = layer1.ls()
            for file_1 in layer1_ls:
                chain = []
                flayer1 = FileOnLayer(file_1, layer1)
                if in_blacklist(file_1):
                    continue
                chain += file_1
                for layer_name2, layer2 in layers_items[layer_num + 1 :]:
                    if not (file_2 := layer2.get(file_1.full_name)):
                        chain += None
                        unsuccessful_chains += chain

                    else:
                        chain += file_2
                        if file_1 != file_2:
                            unsuccessful_chains += chain

        unsuccessful_chains: list[list[FileInfo | None]] = sorted(
            unsuccessful_chains, key=len, reverse=True
        )

        layers_values = list(self.layers.values())
        for chain in unsuccessful_chains:
            source_for_select = []
            targets_for_copy = []
            for layer_num, file1 in enumerate(chain):
                if file1 is None:
                    targets_for_copy += FileOnLayer(None, layers_values[layer_num])
                else:
                    source_for_select += FileOnLayer(file1, layers_values[layer_num])

            if not (source_for_copy := select_newest_files_from(source_for_select)):
                # Не смогли выбрать самые актуальные
                manual_control_needed += chain
            else:
                copy_from(source_for_copy, targets_for_copy)

            # unsuccessful_chains -= chain
            # for layer_num, file1 in enumerate(chain):
            #     if file1 is None:
            #         ...


#
# processed_file = []
# for layer_name1, layer1 in self.layers.items():
#     for file_1 in layer1.ls():  # ls_files(layer1):
#         list_file_on_layers = self.layers.find_file(file_1.full_name)
#         if len(list_file_on_layers) == len(self.layers):
#             # Найден на всех слоях
#             processed_file += file_1
#             continue
#         newest_files = select_newest_resources_from(list_file_on_layers)
#         # for layer_name2, layer2 in self.layers.items():
#         #     layer2.find_file()
#         #     file_on_layer = next(
#         #         (
#         #             file_on_layer
#         #             for file_on_layer in list_file_on_layers
#         #             if file_on_layer.fs == layer2
#         #         ),
#         #         None,
#         #     )  # Поиск файла на слое
#         dt = {}
#         if file_on_layer is None or file_on_layer not in newest_files:
#             # Если файл отсутствует, или он устаревший
#             sources = reasonsable_sources_for_copyfrom(layer2)
#             for sources in sources:
#                 if not layer_available(sources):
#                     continue
#                 sources.cp(
#                     file_1.full_name,
#                 )


class FStab:
    mount_point: str
    "Точка монтирования в VFS" "при одинаковых точках монтирования, FS синхронизуруются"
    fs: BaseFS
    property: dict[str, ty.Any]


class VirtualFS:
    # disk: api.Disk = None
    # manager: ResourceManager = None
    fstab: dict[str, FStab] = {}
    "Пул файловых структур, ключ - уникальный ключ файловой структуры"
    temp_fs: TempFS = None

    _fs_items: dict[BaseFS, list[FileInfo]] = {}
    _hashs: dict[HashOfFile, list[FileInfo]] = {}
    _items: dict[str, tuple[FileInfo, BaseFS]] = {}
    _mpoints: dict[str, list[BaseFS]] = {}
    """
    плоский общий словарь элементов файловых структур пула,
    ключ - хэш элемента, значение - список файлов
    """

    def _calculate_hash_fs(self):
        ...

    def get_hash(self, file: str) -> HashOfFile:
        """
        Вернуть хэш файла
        Parameters
        ----------
        file :

        Returns
        -------

        """
        ...

    def attach_fs(self, fs: BaseFS, key_fs: str, mount_point: str, property: dict = None):
        """
        Присоединить файловую систему к пулу
        Parameters
        ----------
        path : путь к ФС
        fs : ФС

        Returns
        -------

        """
        # self._calculate_hash_fs(fs)

        # ..

    def get_manager(self, path: str) -> BaseFS:
        ...
        # return self.fstab[path]

    #
    # def walk(
    #     self, path: str
    # ) -> ty.Iterable[Resource, ty.Iterable[Resource], ty.Iterable[Resource]]:
    #     """
    #
    #     Parameters
    #     ----------
    #     path :
    #
    #     Returns
    #     -------
    #
    #     """
    #
    #     buffer_files = collections.deque()
    #     buffer_folders = collections.deque()
    #     manager = self.get_manager(path)
    #     root = manager.get(path)
    #
    #     def folders() -> ty.Iterable[Resource]:
    #         nonlocal root
    #         while len(buffer_folders) > 0:
    #             yield buffer_folders.pop()
    #
    #         for item in root.items:
    #             if item.is_folder:
    #                 yield item
    #             else:
    #                 buffer_files.appendleft(item)
    #
    #     def files() -> ty.Iterable[Resource]:
    #         nonlocal root
    #         while len(buffer_files) > 0:
    #             yield buffer_files.pop()
    #
    #         for item in root.items:
    #             if not item.is_folder:
    #                 yield item
    #             else:
    #                 buffer_folders.appendleft(item)
    #
    #     return root, folders(), files()

    def ls(self, path: str) -> ty.Iterable[Resource]:
        manager = self.get_manager(path)
        root = manager.get(path)
        return root.items

    def _cp(self, path: str, target: str, overwrite: bool = False, rm_path_after=False):
        manager_from = self.get_manager(path)
        manager_to = self.get_manager(target)
        if isinstance(manager_from, RemoteFS):
            if isinstance(manager_to, RemoteFS):
                if hasattr(manager_to, "upload_by_url"):
                    manager_to.upload_by_url(path, target)
                else:
                    temp_file = self.temp_fs.create()
                    manager_from.download(path, temp_file)
                    manager_to.cp(temp_file, target)
                    self.temp_fs.rm(temp_file)
            elif isinstance(manager_to, LocalFS):
                manager_from.download(path, target)
            else:
                raise ValueError
        elif isinstance(manager_from, LocalFS):
            if isinstance(manager_to, RemoteFS):
                manager_to.upload(path, target)
            elif isinstance(manager_to, LocalFS):
                manager_from.cp(path, target)
            else:
                raise ValueError
        elif isinstance(manager_from, LocalFS):
            if isinstance(manager_to, RemoteFS):
                manager_to.upload(path, target)
            elif isinstance(manager_to, LocalFS):
                manager_from.cp(path, target)
            else:
                raise ValueError
        else:
            raise ValueError
        if rm_path_after:
            manager_from.rm(path)

    def mv(self, path: str, target: str, overwrite: bool = False):
        self._cp(path, target, overwrite=overwrite, rm_path_after=True)

    def cp(self, path: str, target: str, overwrite: bool = False):
        self._cp(path, target, overwrite=overwrite)

    def rm(self, path: str):
        manager = self.get_manager(path)
        manager.rm(path)

    def mkdir(self, path: str):
        manager = self.get_manager(path)
        manager.mkdir(path)

    def sync(self):
        def processing_file(fs_item):
            ...

        def mount_point_processing(mount_point):
            ...

        for mpoint, fs_list in self._mpoints.items():
            if len(fs_list) < 2:
                continue
            """
            точку монтирования с несколькими ФС синхронизируем
            """
            # for fs in fs_list:
            #     for fi_item in self._fs_items[fs]:
            #         # Для каждого файла, ищем его в других ФС
            #         ignore_fs = [fs]
            #         all_matched = True
            #         fi_processed_local=[fi_item]
            #         for fs_other in fs_list:
            #             if fs_other in ignore_fs:
            #                 continue
            #             fi_item_next = fs_other.get(fi_item.full_name)
            #             fi_processed_local.append(fi_item_next)
            #             if fi_item == fi_item_next:
            #                 # Файл найден и хэши совпали, смотрим дальше, если везде совпадут, вычеркнем этот файл из списка обработки
            #                 # ignore_fs.append(fs_other)
            #                 fi_processed_local.clear()
            #                 continue
            #
            #             all_matched = False
            #         if all_matched:


if __name__ == "__main__":
    import os

    if "YDISK_TOKEN" not in os.environ:
        raise ValueError("Не найдена переменная окружения 'YDISK_TOKEN'")

    _yandex_token = os.environ["YDISK_TOKEN"]

    # disk = DiskAPI.VirtualFS(_yandex_token)
