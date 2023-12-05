from django.shortcuts import render, HttpResponse
from .models import Candle
import pandas as pd, json, asyncio, datetime
from django.core.files.storage import default_storage
from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from django.http import FileResponse


# Create your views here.


async def upload_csv(request):
    if request.method == "POST":
        csv = request.FILES["upload_csv"]
        timeframe = int(request.POST.get("timeframe", 1))
        filename = f"{csv.name.replace('.txt', '')}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        default_storage.save('csv/' + filename + ".txt", csv)
        df = pd.read_csv(csv)
        async_get_candles = sync_to_async(process_data)
        candles = await async_get_candles(df[:timeframe])
        new_df = df[:timeframe]
        converted_candles = await convert_candles(candles)
        final_candle = {
            "BANKNIFTY": new_df["BANKNIFTY"][0],
            "DATE": new_df["DATE"][0],
            "TIME": new_df["TIME"][0],
            "OPEN": new_df["OPEN"][0],
            "HIGH": new_df["HIGH"].max(),
            "LOW": new_df["LOW"].min(),
            "CLOSE": new_df["CLOSE"].iloc[-1],
            "VOLUME": new_df["VOLUME"].iloc[-1],
        }

        json_data = {"final_candle": final_candle, "converted_candles": converted_candles}
        with default_storage.open('json/' + filename + ".json", 'w') as file:
            file.write(json.dumps(json_data, indent=4, default=str))
        file_url = default_storage.url('json/' + filename + ".json")
        print(file_url)
        return render(request, 'result.html', context={"final_candle": final_candle, "timeframe": timeframe, "file_url": file_url})
    else:
        return render(request, 'upload_csv.html')
    

def process_data(df):
    candles = []
    for enum, row in df.iterrows():
        data = {
            "open": row['OPEN'],
            "high": row['HIGH'],
            "low": row['LOW'],
            "close": row['CLOSE'],
            "date": datetime.datetime.strptime(str(row['DATE']), "%Y%m%d").date(),
        }
        candle_obj = Candle.objects.create(**data)
        candles.append(candle_obj)
    return candles


async def convert_candles(candles):
    async def convert(candle):
        candle_json = model_to_dict(candle)
        return candle_json
    tasks = [convert(candle) for candle in candles]
    converted_candles = await asyncio.gather(*tasks)
    return converted_candles


def download_file(request, url):
    path_to_file = "/media/json/nifty_data_2023_12_05_19_34_46.json"
    # response = FileResponse(open(path_to_file, 'rb'))
    with open(path_to_file, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=NiftyData'
        return response