import sys
import unittest
from pathlib import Path
import tempfile
import json
import socket
import os

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'review'))
from catalog_editor import EditorCatalog
from runtime_support import catalog_origin,bind_catalog_server,atomic_json

class CsvReviewTests(unittest.TestCase):
    def test_japanese_candidates_in_all_supported_encodings(self):
        for newline in ('\n','\r\n'):
            for text in ('tag'+newline+'"初音ミク, vocaloid2"'+newline,
                         'tag'+newline+'"初音ミク, vocaloid2 "'+newline):
                for encoding in ('utf-8','utf-8-sig','utf-16','utf-16-be','cp932'):
                    with self.subTest(newline=newline,text=text,encoding=encoding):
                        data=text.encode(encoding)
                        if encoding=='utf-16-be':data=b'\xfe\xff'+data
                        result=EditorCatalog.csv_rows(None,data)
                        self.assertFalse(result['needs_mapping'])
                        self.assertEqual(result['rows'][0]['name'],'初音ミク')
                        self.assertEqual(result['rows'][0]['copyright'],'vocaloid2')
                        self.assertEqual(result['rows'][0]['copy_tags'],text.split(newline)[1].strip('"'))

    def test_invalid_utf16_bom_is_not_silently_reinterpreted(self):
        with self.assertRaises(ValueError):EditorCatalog.csv_rows(None,b'\xff\xfex')

class OriginReviewTests(unittest.TestCase):
    def test_actual_saved_port_is_reused_across_server_instances(self):
        from server import make_server
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first,_=bind_catalog_server(root,0,True,make_server)
            port=first.server_port;first.server_close()
            second,info=bind_catalog_server(root,0,True,make_server)
            try:
                self.assertEqual(second.server_port,port)
                self.assertFalse(info['origin_changed'])
                self.assertEqual(catalog_origin(root)['port'],port)
            finally:second.server_close()

    def test_occupied_saved_port_changes_origin_without_stopping_owner(self):
        from server import make_server
        with tempfile.TemporaryDirectory() as directory, socket.socket() as owner:
            root=Path(directory)
            if os.name=='nt':owner.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            owner.bind(('127.0.0.1',0));owner.listen();port=owner.getsockname()[1]
            atomic_json(root/'outputs/review_origin.json',{'schema_version':1,'requested_port':port,'port':port})
            server,info=bind_catalog_server(root,port,True,make_server)
            try:
                self.assertNotEqual(server.server_port,port)
                self.assertTrue(info['origin_changed'])
                self.assertEqual(info['previous_url'],f'http://127.0.0.1:{port}/')
                with socket.create_connection(('127.0.0.1',port),timeout=1):pass
            finally:server.server_close()

    def test_invalid_saved_ports_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for value in ({'port':True,'requested_port':8790},{'port':70000,'requested_port':8790},{'port':8790,'requested_port':-1}):
                atomic_json(root/'outputs/review_origin.json',{'schema_version':1,**value})
                self.assertEqual(catalog_origin(root),{})

    def test_non_bind_errors_are_not_hidden_by_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            calls=[]
            def factory(root,port):
                calls.append(port)
                raise OSError(5,'unrelated failure')
            with self.assertRaises(OSError):bind_catalog_server(Path(directory),8790,True,factory)
            self.assertEqual(calls,[8790])
