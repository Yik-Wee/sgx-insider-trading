from forms import NotificationForm1


def main():
    with open("./pdfs/XFA_form1.pdf", "rb") as f:
        print(f.name)
        form1 = NotificationForm1(f)
        print(form1)

    print("======")
    with open("./pdfs/sgx_form1_part2_xfa.pdf", "rb") as f:
        print(f.name)
        form2 = NotificationForm1(f)
        print(form2)

    print("======")
    with open("./pdfs/SingTel_20130621_Form1.pdf", "rb") as f:
        print(f.name)
        form3 = NotificationForm1(f)
        print(form3)


if __name__ == "__main__":
    main()
