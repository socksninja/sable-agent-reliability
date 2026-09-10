export default function handler(req, res) {
  res.status(200).json({
    service: "sable-verifier",
    schema_version: "sable.verifier_service.v2.8",
    status: "ok",
  });
}
