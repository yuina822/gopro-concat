#!/usr/bin/env python3
import ffmpeg
import argparse
import os
import glob
import gpmf
import gpxpy

def group_videos(path: str) -> list:
    """ GoPro録画データのグルーピング
    Parameters
    ----------
    path: GoPro録画データディレクトリパス

    Returns
    -------
    group_list: GoPro録画データグループ化リスト

    """
    mode = ['GX', 'GH']
    group_list = []
    for m in mode:
        rec = glob.glob(path + '/' + m + '*.MP4')
        if len(rec) == 0:
            continue

        index = set()
        for r in rec:
            index.add(r[-7:-4])

        for i in index:
            g = glob.glob(path + '/' + m +'*' + i + '.MP4')
            group_list.append(sorted(g))

    if len(group_list) == 0:
        raise ValueError()

    return group_list

def cocat_videos(input_videos: list, output_path: str):
    """ GoPro録画データの結合
    Parameters
    ----------
    input_videos: GoPro録画データファイルパス
        結合したいGoPro録画データファイルパスのリスト
    output_path: 結合後録画データの保存先のディレクトリ

    """

    header_name = input_videos[0]
    output_name = header_name[-12:]
    ffmpeg.input('concat:' + '|'.join(input_videos)).output(output_path + '/' + output_name, c='copy').run()

def extract_gps(input_videos: list, output_path: str):
    """ GoPro GPSデータの結合
    Parameters
    ----------
    input_videos: GoPro録画データファイルパス
        結合したいGoPro録画データファイルパスのリスト
    output_path: 結合後GPXデータの保存先のディレクトリ

    """

    header_name = input_videos[0]
    output_name = header_name[-12:].replace('MP4', 'gpx')

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    for v in input_videos:
        stream = gpmf.io.extract_gpmf_stream(v)

        gps_blocks = gpmf.gps.extract_gps_blocks(stream)

        try:
            gps_data = list(map(gpmf.gps.parse_gps_block, gps_blocks))
            gpx_track.segments.append(gpmf.gps.make_pgx_segment(gps_data))
        except ValueError:
            print('GPS data is not contained: ', v)
        except IndexError:
            print('gpmf\'s bug: ', v)

    gpx_file_path = output_path + '/' + output_name

    with open(gpx_file_path, mode='w') as f:
        f.write(gpx.to_xml())

def main():
    parser = argparse.ArgumentParser(description='GoPro録画データ結合スクリプト')
    parser.add_argument('-i', '--input', help='録画データディレクトリ')
    parser.add_argument('-o', '--output', help='保存先ディレクトリ')

    args = parser.parse_args()
    groups = group_videos(args.input)
    for g in groups:
        extract_gps(g, args.output)
        cocat_videos(g, args.output)

if __name__ == "__main__":
    main()
