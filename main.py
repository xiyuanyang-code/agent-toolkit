def test_importing_packages():
    try:
        from data_generation import DataGenerationPipeline
    except Exception as e:
        print(f"Error Occurred: {e}")


if __name__ == "__main__":
    test_importing_packages()
    print("Hello World")