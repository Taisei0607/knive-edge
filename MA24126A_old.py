"""
MA08/MA24108A パワーセンサー制御クラス
================================================================================
このモジュールは、MA08およびMA24108Aパワーセンサーをシリアル/USB通信で
制御するための汎用クラスを提供します。

Python Ver.: 3.8以上推奨
作成日: 2025/10/23
================================================================================
"""

import serial
import time


class PowerSensor:
    """
    MA08/MA24108A パワーセンサー制御クラス
    
    シリアル通信またはUSB通信を介してパワーセンサーと通信し、
    パワー測定、各種設定を行うための汎用クラスです。
    """
    
    def__init__(self, port = "cu.usbmodem11401", baudrate = 19200, timeout = 1.0):
        """
        PowerSensorクラスの初期化
        
        Parameters
        ----------
        port : str, optional
            COMポート名 (デフォルト: "COM5")
            Linuxの場合は "/dev/ttyUSB0" など
        baudrate : int, optional
            ボーレート (デフォルト: 19200)
        timeout : float, optional
            タイムアウト時間[秒] (デフォルト: 1.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        
        # シリアルポートを初期化
        self._init_serial()
    
    def_init_serial(self):
        """
        シリアルポートの初期化
        """
        try:
            self.ser = serial.Serial(
                port = self.port,
                baudrate = self.baudrate,
                bytesize = 7,  # データビット数: 7bit
                parity = serial.PARITY_NONE,  # パリティなし
                stopbits = 1, # ストップビット: 1bit
                timeout = self.timeout
            )
            print(f"Connected to {self.port}")
        except serial.SerialException as e:
            print(f"Error: シリアルポート接続に失敗しました: {e}")
            raise
    
    def close(self):
        """
        シリアルポートを閉じる
        
        Returns
        -------
        bool
            正常終了時True
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Disconnected from {self.port}")
        return True
    
    def write(self, command):
        """
        コマンドを送信する
        
        Parameters
        ----------
        command : str
            送信するコマンド（改行文字を含む）
        
        Returns
        -------
        bool
            正常送信時True
        """
        if not self.ser or not self.ser.is_open:
            print("Error: シリアルポートが開いていません")
            return False
        
        try:
            self.ser.write(command.encode())
            return True
        except serial.SerialException as e:
            print(f"Error: コマンド送信に失敗しました: {e}")
            return False
    
    def read(self, size = 1024):
        """
        レスポンスを読み取る
        
        Parameters
        ----------
        size : int, optional
            読み取るバイト数 (デフォルト: 1024)
        
        Returns
        -------
        str
            受信したデータ（文字列）
        """
        if not self.ser or not self.ser.is_open:
            print("Error: シリアルポートが開いていません")
            return ""
        
        try:
            response = self.ser.read(size).decode().strip()
            return response
        except serial.SerialException as e:
            print(f"Error: データ読み取りに失敗しました: {e}")
            return ""
    
    def query(self, command, size = 1024):
        """
        コマンドを送信してレスポンスを受信する
        
        Parameters
        ----------
        command : str
            送信するコマンド（改行文字を含む）
        size : int, optional
            読み取るバイト数（デフォルト: 1024）
        
        Returns
        -------
        str
            受信したレスポンス（文字列）
        """
        self.write(command)
        time.sleep(0.05) # 短い待機時間
        return self.read(size)
    
    # ================================================================================
    # 基本コマンド
    # ================================================================================
    
    def get_id(self):
        """
        機器のID情報を取得する
        
        Returns
        -------
        str
            機器ID文字列
        """
        return self.query("IDN?\n")
    
    def start(self):
        """
        測定を開始する
        
        Returns
        -------
        bool
            コマンド送信成功時True
        """
        return self.write("START\n")
    
    def stop(self):
        """
        測定を停止する
        
        Returns
        -------
        bool
            コマンド送信成功時True
        """
        return self.write("STOP\n")
    
    # ================================================================================
    # 校正
    # ================================================================================
    
    def zero_calibration(self, show_progress = True):
        """
        ゼロ校正を実行する
        
        Parameters
        ----------
        show_progress : bool, optional
            進捗を表示するか (デフォルト: True)
        
        Returns
        -------
        bool
            校正完了時True
        """
        if show_progress:
            print("\nZero calibration start...")
        
        self.write("ZERO\n")
        
        # 校正には約20秒かかる
        if show_progress:
            for i in range(21):
                progress = min(i*5, 100)
                print(f"\rProgress: {progress}%", end = "")
                time.sleep(1.0)
            print("\rProgress: 100%")
            print("Zero calibration finished.\n")
        else:
            time.sleep(20)
        
        return True
    
    # ================================================================================
    # パワー測定
    # ================================================================================
    
    def get_power(self):
        """
        現在のパワー値を取得する
        
        Returns
        -------
        float or None
            パワー値[dBm]、エラー時はNone
        """
        response = self.query("PWR?\n")
        try:
            return float(response)
        except ValueError:
            print(f"Error: パワー値の取得に失敗しました (Response: {response})")
            return None
    
    def measure_power(self, display = True):
        """
        パワーを測定して表示する
        
        Parameters
        ----------
        display : bool, optional
            結果を表示するか (デフォルト: True)
        
        Returns
        -------
        float or None
            パワー値[dBm]
        """
        power = self.get_power()
        if power is not None and display:
            print(f"Power: {power:.2f} dBm")
        return power
    
    # ================================================================================
    # 周波数設定
    # ================================================================================
    
    def get_frequency(self):
        """
        現在の中心周波数を取得する
        
        Returns
        -------
        float or None
            中心周波数[GHz]、エラー時はNone
        """
        response = self.query("FREQ?\n")
        try:
            return float(response)
        except ValueError:
            print(f"Error: 周波数の取得に失敗しました (Response: {response})")
            return None
    
    def set_frequency(self, freq_ghz):
        """
        中心周波数を設定する
        
        Parameters
        ----------
        freq_ghz : float
            中心周波数[GHz]
        
        Returns
        -------
        bool
            設定成功時True
        """
        command = f"FREQ {freq_ghz:.3f}\n"
        response = self.query(command)
        
        if response == "OK":
            print(f"Frequency set to {freq_ghz:.3f} GHz")
            return True
        else:
            print(f"Error: 周波数設定に失敗しました (Response: {response})")
            return False
    
    # ================================================================================
    # アパーチャ時間設定
    # ================================================================================
    
    def get_aperture_time(self):
        """
        現在のアパーチャ時間を取得する
        
        Returns
        -------
        float or None
            アパーチャ時間[ms]、エラー時はNone
        """
        response = self.query("CHAPERT?\n")
        try:
            return float(response)
        except ValueError:
            print(f"Error: アパーチャ時間の取得に失敗しました (Response: {response})")
            return None
    
    def set_aperture_time(self, time_ms):
        """
        アパーチャ時間を設定する
        
        Parameters
        ----------
        time_ms : float
            アパーチャ時間[ms] (範囲: 0.01 ~ 300)
        
        Returns
        -------
        bool
            設定成功時True
        """
        if time_ms < 0.01 or time_ms > 300:
            print(f"Error: アパーチャ時間は 0.01 ~ 300 ms の範囲で設定してください")
            return False
        
        command = f"CHAPERT {time_ms:.2f}\n"
        response = self.query(command)
        
        if response == "OK":
            print(f"Aperture time set to {time_ms:.2f} ms")
            return True
        else:
            print(f"Error: アパーチャ時間設定に失敗しました (Response: {response})")
            return False
    
    # ================================================================================
    # 平均化設定
    # ================================================================================
    
    def get_average_mode(self):
        """
        現在の平均化方式を取得する
        
        Returns
        -------
        str or None
            "Moving" (移動法) または "Repeat" (繰り返し法)、エラー時はNone
        """
        response = self.query("AVGTYP?\n")
        
        if response == "0":
            return "Moving"
        elif response == "1":
            return "Repeat"
        else:
            print(f"Error: 平均化方式の取得に失敗しました (Response: {response})")
            return None
    
    def set_average_mode(self, mode):
        """
        平均化方式を設定する
        
        Parameters
        ----------
        mode : str or int
            "Moving" or 0: 移動平均法
            "Repeat" or 1: 繰り返し法
        
        Returns
        -------
        bool
            設定成功時True
        """
        if mode == "Moving" or mode == 0:
            command = "AVGTYP 0\n"
            mode_str = "Moving"
        elif mode == "Repeat" or mode == 1:
            command = "AVGTYP 1\n"
            mode_str = "Repeat"
        else:
            print("Error: 平均化方式は 'Moving' または 'Repeat' を指定してください")
            return False
        
        response = self.query(command)
        
        if response == "OK":
            print(f"Average mode set to {mode_str}")
            return True
        else:
            print(f"Error: 平均化方式設定に失敗しました (Response: {response})")
            return False
    
    def get_average_count(self):
        """
        現在の平均化回数を取得する
        
        Returns
        -------
        int or None
            平均化回数、エラー時はNone
        """
        response = self.query("AVGCNT?\n")
        try:
            return int(response)
        except ValueError:
            print(f"Error: 平均化回数の取得に失敗しました (Response: {response})")
            return None
    
    def set_average_count(self, count):
        """
        平均化回数を設定する
        
        Parameters
        ----------
        count : int
            平均化回数 (範囲: 1 ~ 1024)
        
        Returns
        -------
        bool
            設定成功時True
        """
        if count < 1 or count > 1024:
            print("Error: 平均化回数は 1 ~ 1024 の範囲で設定してください")
            return False
        
        command = f"AVGCNT {count}\n"
        response = self.query(command)
        
        if response == "OK":
            print(f"Average count set to {count}")
            return True
        else:
            print(f"Error: 平均化回数設定に失敗しました (Response: {response})")
            return False
    
    # ================================================================================
    # 便利な関数
    # ================================================================================
    
    def initialize(self, freq_ghz = None, aperture_ms = None, avg_mode = None, avg_count = None):
        """
        センサーを初期化する
        
        Parameters
        ----------
        freq_ghz : float, optional
            中心周波数[GHz]
        aperture_ms : float, optional
            アパーチャ時間[ms]
        avg_mode : str or int, optional
            平均化方式 ("Moving" or "Repeat")
        avg_count : int, optional
            平均化回数
        
        Returns
        -------
        bool
            初期化成功時True
        """
        print("\nInitializing sensor...")
        
        # 機器ID確認
        device_id = self.get_id()
        print(f"Device ID: {device_id}")
        
        # 各種設定
        if freq_ghz is not None:
            self.set_frequency(freq_ghz)
        
        if aperture_ms is not None:
            self.set_aperture_time(aperture_ms)
        
        if avg_mode is not None:
            self.set_average_mode(avg_mode)
        
        if avg_count is not None:
            self.set_average_count(avg_count)
        
        print("Initialization complete.\n")
        return True
    
    def show_settings(self):
        """
        現在の設定を表示する
        """
        print("\n=== Current Settings ===")
        
        freq = self.get_frequency()
        if freq is not None:
            print(f"Frequency: {freq:.3f} GHz")
        
        aperture = self.get_aperture_time()
        if aperture is not None:
            print(f"Aperture Time: {aperture:.2f} ms")
        
        avg_mode = self.get_average_mode()
        if avg_mode is not None:
            print(f"Average Mode: {avg_mode}")
        
        avg_count = self.get_average_count()
        if avg_count is not None:
            print(f"Average Count: {avg_count}")
        
        print("========================\n")