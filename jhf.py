#!/usr/bin/env python3
from requests_html import HTMLSession
import requests
import random
from sys import argv
from string import hexdigits
import lxml_html_clean

CLEAN_LINE = "\033[1K\r"
GREEN_COLOR = "\033[42;30m"
RED_COLOR = "\033[101;30m"
NORMAL_COLOR = "\033[0m"


class JackHashFinder:
    def __init__(self):
        self.session = HTMLSession()
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                      'like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    @staticmethod
    def detect_hash(hash_to_detect):
        for letter in hash_to_detect:
            if letter not in hexdigits:
                return None
        hash_len = len(hash_to_detect)
        database = {
            32: "md5",
            40: "sha1",
            41: "MySQL",
            64: "sha256",
            96: "sha384",
            128: "sha512"
        }
        detected = database.get(hash_len, None)
        if detected == 'MySQL' and not hash_to_detect.startswith("*"):
            return None
        return detected

    def hashes_com(self, hash_to_find):
        supported_hashes = ["md5", "sha1", "MySQL", "NTLM", "sha256", "sha512"]
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None
        
        get_result = self.session.get("https://hashes.com/en/decrypt/hash", headers=self.headers)
        csrf_token = get_result.html.find("input[name=csrf_token]", first=True).attrs.get('value', None)
        
        post_result = self.session.post("https://hashes.com/en/decrypt/hash",
            headers=self.headers,
            data={
                'csrf_token':csrf_token,
                'hashes':hash_to_find,
                'vyd':64,
                'submitted': True
            }
        )
        
        if "0 found" in post_result.text:
            return None
        else:
            hash_result = post_result.html.find('div[class=py-1]', first=True)
            if hash_result:
                return hash_result.text.split(hash_to_find+":")[1]
        
    def md5decrypt_net(self, hash_to_find):
        supported_hashes = ['md5', 'sha1', 'sha256', 'sha384', 'sha512']
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None

        url = "https://md5decrypt.net/"
        if hash_type != 'md5':
            url += 'en/%s/' % hash_type.capitalize()

        post_r = self.session.post(url=url, data={'hash': hash_to_find, 'decrypt': 'Decrypt'}, headers=self.headers)
        if "Too much connections" in post_r.text:
            return None

        data = post_r.html.find('b', first=True)
        if data:
            return data.text
        return None

    def gromweb_com(self, hash_to_find):
        supported_hashes = ["md5", "sha1"]
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None

        if hash_type == "sha1":
            url = "https://sha1.gromweb.com/?hash=%s"
        else:
            url = "https://md5.gromweb.com/?md5=%s"

        get_r = self.session.get(url=url % hash_to_find, headers=self.headers)

        if "no reverse string was found." in get_r.text:
            return None

        hash_result = get_r.html.find("em[class='long-content string']", first=True)
        if hash_result:
            return hash_result.text

        return None

    def hashtoolkit_com(self, hash_to_find):
        supported_hashes = ["md5", "sha1", "sha256", "sha384", "sha512"]
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None
        get_r = self.session.get(url="https://hashtoolkit.com/decrypt-hash/?hash=%s" % hash_to_find,
                                 headers=self.headers)
        if "No hashes found for" in get_r.text:
            return None
        
        hash_result = get_r.html.find("span[title~='decrypted']", first=True)

        if hash_result:
            return hash_result.text
        return None

    def md5online_it(self, hash_to_find):
        supported_hashes = ["md5"]
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None
        r = self.session.get("http://www.md5online.it/index.lm?key_decript=%s" % hash_to_find, headers=self.headers)
        hash_result = r.html.find("font[style='font-size: 20px; color:#004030;']", first=True)
        if hash_result:
            result = hash_result.text.split("\n")[0]
            if result == "NESSUN RISULTATO":
                return None
            return result
        return None
    
    def passwordrecovery_io(self, hash_to_find):
        supported_hashes = ["md5", "sha1", "sha256", "sha512", "cisco"]
        hash_type = self.detect_hash(hash_to_find)
        if hash_type not in supported_hashes:
            return None
        
        csrf_get = self.session.get("https://passwordrecovery.io/"+hash_type, headers=self.headers)
        csrf_token = csrf_get.html.find("input[name=csrf_token]", first=True).attrs.get('value', None)
        if not csrf_token:
            return None
        
        get_result = self.session.post("https://passwordrecovery.io/query/"+hash_type, headers=self.headers, data={
            'csrf_token': csrf_token,
            'hash': hash_to_find
        })

        result = get_result.html.find("div[class='notification is-link']", first=True)
        if result:
            return result.text.split("The hash is: ")[1]
        return None

    def decrypt_methods(self):
        return [self.hashtoolkit_com, self.md5online_it, self.gromweb_com, self.md5decrypt_net, self.hashes_com, self.passwordrecovery_io]


def initialize(hashes_to_find, print_result=False):
    cracker = JackHashFinder()

    for hash_to_find in hashes_to_find:
        found = False
        for req in cracker.decrypt_methods():
            if print_result:
                print(CLEAN_LINE, "Trying", hash_to_find, "with", req.__name__, end=" ", flush=True)

            result = req(hash_to_find)
            if result:
                if print_result:
                    print("%s %s: %s%s%s" % (CLEAN_LINE, hash_to_find, GREEN_COLOR, result, NORMAL_COLOR))
                    found = True
                else:
                    yield hash_to_find, result
                break
        if not found and print_result:
            print("%s %s: %sNot Found%s" % (CLEAN_LINE, hash_to_find, RED_COLOR, NORMAL_COLOR))


def print_data(hashes_to_find):
    for _ in initialize(hashes_to_find, True):
        continue


def yield_from_file(filepath):
    with open(filepath, "r") as f:
        for line in f:
            yield line.rstrip()


def main():
    if not argv[1:]:
        print("Supply hashe(s) or use --file/-f to specify the file to read")
        return

    try:
        if argv[1] in ["--file", "-f"]:
            print_data(yield_from_file(argv[2]))
            return
    except IndexError:
        print("Supply hashe(s) or use --file/-f to specify the file to read")
        return

    print_data(argv[1:])


if __name__ == "__main__":
    main()
