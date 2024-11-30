
# Forex Breakout Identification (Multiclass)

This repository contains a machine learning project aimed at identifying breakouts in the forex market using a multiclass classification approach. The goal of this project was to predict potential market breakout movements and classify them into distinct categories to inform trading strategies.

## Features of the Project

- **Data Preprocessing:** Includes methods for preparing forex data for machine learning, such as normalization and feature engineering.
- **Machine Learning Models:** Implements and compares several multiclass classification models to predict breakout events.
- **Performance Evaluation:** Includes metrics and visualizations to assess the accuracy and robustness of the models.

## Observations

While the model demonstrated excellent predictive accuracy during testing, the real-world application revealed a significant limitation:  
The losses incurred when the model made incorrect predictions were much greater than the gains achieved from correct predictions. This imbalance caused the overall trading strategy based on the model to be unprofitable.

## Conclusion

This project highlights the importance of not only achieving high accuracy in predictive models but also understanding the risk-reward dynamics of trading systems. Future work could involve optimizing the model for risk management or exploring alternative strategies for breakout identification.

## License

This project is open source and available under the [MIT License](LICENSE).
