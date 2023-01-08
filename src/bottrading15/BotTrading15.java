/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package bottrading15;

import com.binance.api.client.BinanceApiClientFactory;
import com.binance.api.client.BinanceApiRestClient;
import com.binance.api.client.domain.OrderSide;
import com.binance.api.client.domain.OrderType;
import com.binance.api.client.domain.market.Candlestick;
import com.binance.api.client.domain.market.CandlestickInterval;
import java.util.ArrayList;
import java.util.List;

/**
 *
 * @author diego
 */
public class BotTrading15 {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {




 
        // Crea una nueva instancia de BinanceApiRestClient
        BinanceApiClientFactory factory = BinanceApiClientFactory.newInstance();
        BinanceApiRestClient client = factory.newRestClient();

        // Establece el par de divisas y el intervalo de tiempo a utilizar para calcular la media móvil
        String symbol = "BTCUSDT";
        CandlestickInterval interval = CandlestickInterval.HOURLY;

        // Obtiene los últimos 500 candeleros para el par de divisas y el intervalo especificados
        List<Candlestick> candlesticks = client.candlesticks(symbol, interval, 500, null, null);

        // Calcula las medias móviles para las últimas 50 y 100 velas
        List<Double> ma50 = calculateMovingAverage(candlesticks, 50);
        List<Double> ma100 = calculateMovingAverage(candlesticks, 100);
        List<Double> closePrices = getClosePrices(candlesticks);

        while (true) {
            for (int i = 0; i < candlesticks.size(); i++) {
                // Obtiene las medias móviles y el precio de cierre para la vela actual
                double ma50Value = ma50.get(i);
                double ma100Value = ma100.get(i);
                double closePrice = closePrices.get(i);

                // Verifica si se ha producido un cruce alcista
                if (ma50Value > ma100Value && ma50Value > closePrice) {
                    // Se ha producido un cruce alcista, enviar orden de compra
                    sendBuyOrder(symbol, closePrice);
                }

                // Verifica si se ha producido un cruce bajista
                else if (ma50Value < ma100Value && ma50Value < closePrice) {
                    // Se ha producido un cruce bajista, enviar orden de venta
                    sendSellOrder(symbol, closePrice);
                }
            }

            // Hace que el programa se detenga por un minuto antes de continuar con la siguiente iteración
            Thread.sleep(60 * 1000);
        }
    }

    private static List<Double> calculateMovingAverage(List<Candlestick> candlesticks, int period) {
    
    // Crea una lista para almacenar los valores de la media móvil
    List<Double> movingAverages = new ArrayList<>();

    // Calcula la media móvil para cada vela en la lista
    for (int i = 0; i < candlesticks.size(); i++) {
        // Obtiene el precio de cierre de la vela actual
        double close = candlesticks.get(i).getClose();

        // Calcula el total acumulado de los últimos "period" precios de cierre
        double sum = 0;
        for (int j = i - period + 1; j <= i; j++) {
            sum += candlesticks.get(j).getClose();
        }

        // Calcula la media móvil y agrega el resultado a la lista
        double movingAverage = sum / period;
        movingAverages.add(movingAverage);
    }

    // Devuelve la lista con los valores de la media móvil
    return movingAverages;
}
    
    
    // Crea una lista para almacenar los valores de la media móvil
    List<Double> movingAverages = new ArrayList<>();

    // Calcula la media móvil para cada vela en la lista
    for (int i = 0; i < candlesticks.size(); i++) {
        // Obtiene el precio de cierre de la vela actual
        double close = candlesticks.get(i).getClose();

        // Calcula el total acumulado de los últimos "period" precios de cierre
        double sum = 0;
        for (int j = i - period + 1; j <= i; j++) {
            sum += candlesticks.get(j).getClose();
        }

        // Calcula la media móvil y agrega el resultado a la lista
        double movingAverage = sum / period;
        movingAverages.add(movingAverage);
    }

    // Devuelve la lista con los valores de la media móvil
    return movingAverages;
}

    }

    private static List<Double> getClosePrices(List<Candlestick> candlesticks) {
   
    // Crea una lista para almacenar los precios de cierre
    List<Double> closePrices = new ArrayList<>();

    // Itera a través de la lista de velas y agrega el precio de cierre a la lista
    for (Candlestick candle : candlesticks) {
        closePrices.add(candle.getClose());
    }

    // Devuelve la lista con los precios de cierre
    return closePrices;

    // Implementación para obtener los precios de cierre de las velas
        // ...
    }

 
    private static void sendBuyOrder(String symbol, double price) {
    // Crea una nueva instancia de BinanceApiRestClient
    BinanceApiClientFactory factory = BinanceApiClientFactory.newInstance();
    //BinanceApiRestClient client = factory.newRestClient();

    // Establece la cantidad de moneda a comprar
    String quantity = "0.1";

    // Envía la orden de compra
    client.newOrder(symbol, OrderSide.BUY, OrderType.MARKET, quantity, price, TimeInForce.GTC, null, null, null, null);
}

    

   
    private static void sendSellOrder(String symbol, double price) {
    // Crea una nueva instancia de BinanceApiRestClient
    //BinanceApiClientFactory factory = BinanceApiClientFactory.newInstance();
    //BinanceApiRestClient client = factory.newRestClient();

    // Establece la cantidad de moneda a vender
    String quantity = "0.1";

    // Envía la orden de venta
    client.newOrder(symbol, OrderSide.SELL, OrderType.MARKET, quantity, price, TimeInForce.GTC, null, null, null, null);
    // Implementación del método para enviar una orden de venta
        // ...



    }
    
}
