def generate_log_config(dir='log', template='default'):
    if template.lower() == 'default':
        return {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s.%(msecs)03d [%(levelname)s][%(threadName)s] [%(module)s:%(funcName)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "brief": {
                    "format": "%(asctime)s.%(msecs)03d [%(levelname)s][%(threadName)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "filters": {
            },
            "handlers": {
                "file_debug": {
                    "level": "DEBUG",
                    "class": "jtrader.core.common.log.AdvancedRotatingFileHandler",
                    "filename": f"{dir}/debug_%Y%m%d_%H%M%S.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "formatter": "standard"
                },
                "file_info": {
                    "level": "INFO",
                    "class": "jtrader.core.common.log.AdvancedRotatingFileHandler",
                    "filename": f"{dir}/info_%Y%m%d_%H%M%S.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "formatter": "standard"
                },
                "file_error": {
                    "level": "ERROR",
                    "class": "jtrader.core.common.log.AdvancedRotatingFileHandler",
                    "filename": f"{dir}/error_%Y%m%d_%H%M%S.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "formatter": "standard"
                },
                "email": {
                    "level": "WARN",
                    "class": "jtrader.core.common.log.TlsSMTPHandler",
                    "mailhost": ["smtp.gmail.com", 587],
                    "fromaddr": "your_email@gmail.com",
                    "toaddrs": ["your_email@gmail.com"],
                    "subject": "Notification from jtrader",
                    "credentials": ["your_email@gmail.com", "your_password"]
                },
                "console": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "brief"
                }
            },
            "loggers": {
                "jtrader": {
                    "handlers": [
                        "file_debug",
                        "file_info",
                        "email",
                        "console"
                    ],
                    "level": "DEBUG",
                    "propagate": True
                }
            }
        }
    elif template.lower() == 'test':
        return {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s.%(msecs)03d [%(levelname)s][%(threadName)s] [%(module)s:%(funcName)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "brief": {
                    "format": "%(asctime)s.%(msecs)03d [%(levelname)s][%(threadName)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "filters": {
            },
            "handlers": {
                "debug_info": {
                    "level": "DEBUG",
                    "class": "jtrader.core.common.log.AdvancedRotatingFileHandler",
                    "filename": f"{dir}/debug_%Y%m%d_%H%M%S.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "formatter": "standard"
                },
                "console": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "brief"
                }
            },
            "loggers": {
                "jtrader": {
                    "handlers": [
                        "file_info",
                        "console"
                    ],
                    "level": "DEBUG",
                    "propagate": True
                }
            }
        }
    else:
        return {
            "version": 1,
            "disable_existing_loggers": True,
        }
