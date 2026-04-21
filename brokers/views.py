# brokers/views.py
class VWorldSequentialSyncView(APIView):
    """
    사무소 저장 완료 후 → 해당 사무소의 중개업자 자동 저장
    GET /api/brokers/vworld/sync/?ld_code=11110
    """

    def get(self, request):
        ld_code = request.query_params.get("ld_code", "")
        jurirno = request.query_params.get("jurirno", "")
        client  = VWorldDataClient()
        report  = {"offices": {}, "brokers": {}}

        # ── STEP 1 : 사무소 데이터 먼저 저장 ──────────────
        try:
            office_result = client.get_offices(
                ld_code=ld_code, jurirno=jurirno
            )
        except Exception as e:
            return _err(e)

        saved_offices = []
        for props in office_result["features"]:
            ser = VWorldOfficeRawSerializer(data=props)
            if ser.is_valid():
                saved_offices.append(ser.save())

        report["offices"] = {
            "total":  office_result["total"],
            "saved":  len(saved_offices),
        }

        # ── STEP 2 : 저장된 사무소의 등록번호로 중개업자 조회 ──
        saved_brokers = []
        errors        = []

        for office in saved_offices:
            try:
                broker_result = client.get_brokers(jurirno=office.jurirno)
            except Exception as e:
                errors.append({"jurirno": office.jurirno, "error": str(e)})
                continue

            for props in broker_result["features"]:
                ser = VWorldBrokerRawSerializer(data=props)
                if ser.is_valid():
                    broker = ser.save()
                    # FK 자동 연결
                    if not broker.office:
                        broker.office = office
                        broker.save(update_fields=["office"])
                    saved_brokers.append(broker.id)
                else:
                    errors.append(ser.errors)

        report["brokers"] = {
            "saved":  len(saved_brokers),
            "errors": len(errors),
        }

        return Response({
            "message": "사무소 → 중개업자 순서로 동기화 완료",
            "report":  report,
        })