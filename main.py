import asyncio
import argparse
import time
import sys
import httpx

async def measure_speed(url: str, num_requests: int, proxy: str | None = None) -> None:
    total_bytes = 0
    total_time = 0.0

    print("🚀 Начинаем тестирование...")
    print(f"🔗 URL: {url}")
    if proxy:
        print(f"🛡️  Используется прокси: {proxy}")
    print(f"🔄 Количество запросов: {num_requests} (выполняются строго последовательно)\n")

    timeout = httpx.Timeout(60.0)
    
    async with httpx.AsyncClient(timeout=timeout, proxy=proxy) as client:
        for i in range(1, num_requests + 1):
            try:
                # Оповещаем о начале запроса
                print(f"⏳ [ {i}/{num_requests} ] Подключение к серверу...", end="\r", flush=True)
                
                start_time = time.perf_counter()
                content_length = 0
                last_print_bytes = 0
                
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    
                    # Читаем увеличенными чанками по 64 KB для лучшей пропускной способности
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        content_length += len(chunk)
                        
                        # Обновляем консоль примерно каждые 1 МБ (чтобы не тормозить I/O операциями print)
                        if content_length - last_print_bytes >= 1024 * 1024:
                            mb_current = content_length / (1024 * 1024)
                            # Имитация прогресса в реальном времени с перезаписью строки (\r)
                            print(f"⏳ [ {i}/{num_requests} ] В процессе... Скачано: {mb_current:.1f} MB", end="\r", flush=True)
                            last_print_bytes = content_length
                            
                req_time = time.perf_counter() - start_time
                total_time += req_time
                total_bytes += content_length
                
                mb_downloaded = content_length / (1024 * 1024)
                
                # Финальный принт запроса (затираем временную строку пробелами, чтобы не осталось хвостов)
                clear_padding = " " * 15
                print(f"✅ [ {i}/{num_requests} ] Завершено: {req_time:.2f} сек. | Объем: {mb_downloaded:.2f} MB{clear_padding}")
                
            except httpx.RequestError as e:
                print(f"\n❌ Ошибка сети при запросе {i}: {e}")
                sys.exit(1)
            except httpx.HTTPStatusError as e:
                print(f"\n❌ Сервер вернул ошибку {e.response.status_code} при запросе {i}")
                sys.exit(1)

    if num_requests > 0 and total_time > 0:
        avg_time = total_time / num_requests
        total_mb = total_bytes / (1024 * 1024)
        avg_speed_mb_s = total_mb / total_time
        avg_speed_mbps = avg_speed_mb_s * 8

        print("\n" + "="*40)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
        print("="*40)
        print(f"📦 Общий объем скачанных данных: {total_mb:.2f} Мегабайт (MB)")
        print(f"⏱  Среднее время одного запроса: {avg_time:.2f} секунд")
        print(f"🚀 Средняя скорость скачивания:  {avg_speed_mb_s:.2f} Мегабайт/сек (MB/s)")
        print(f"                                 {avg_speed_mbps:.2f} Мегабит/сек (Mbps)")
        print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Асинхронная CLI утилита для замера скорости скачивания файла по сети."
    )
    parser.add_argument("url", type=str, help="URL адрес для скачивания (например, прямая ссылка на тяжелую картинку)")
    parser.add_argument("--requests", type=int, default=10, help="Количество последовательных запросов (по умолчанию: 10)")
    parser.add_argument("--proxy", type=str, default=None, help="URL прокси-сервера (например: socks5h://127.0.0.1:1080)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(measure_speed(args.url, args.requests, args.proxy))
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем.")

